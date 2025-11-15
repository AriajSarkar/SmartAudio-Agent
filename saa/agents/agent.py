"""
Audiobook Pipeline - Custom Agent with Deterministic 5-Stage Workflow

ARCHITECTURE PHILOSOPHY:
- Tools = Actions (extract, clean, synthesize)
- Gemini = Intelligence (decisions, structure, judgment)
- Agents = Orchestrators combining intelligence + tools

This Custom Agent inherits from BaseAgent and implements _run_async_impl
for guaranteed execution order and robust error handling.
"""
import logging
from pathlib import Path
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models import Gemini
from typing_extensions import override

from saa.config import get_settings
from saa.utils import get_gpu_info, setup_logger
from saa.tools.document_tools import extract_text_from_txt, extract_text_from_pdf, get_document_metadata
from saa.tools.text_tools import clean_text, filter_unwanted_content, segment_text
from saa.tools.voice_tools import detect_characters, analyze_text_gender, assign_voice_profile
from saa.tools.tts_tools import synthesize_audio, cleanup_tts_resources
from saa.tools.audio_tools import merge_audio_chunks, normalize_audio, export_audio_format, get_audio_info

# Setup structured logging
logger = setup_logger(
    name="audiobook_pipeline",
    level=logging.INFO,
    log_file="logs/pipeline.log"
)
settings = get_settings()


class AudiobookPipelineAgent(BaseAgent):
    """
    Professional-grade Custom Agent for audiobook generation.
    
    Implements deterministic 5-stage pipeline with:
    - Guaranteed stage execution (no LLM skipping steps)
    - Intelligent decision-making via Gemini-powered sub-agents
    - Robust error handling with automatic retries
    - State validation between stages
    """
    
    # Declare sub-agents (Pydantic fields)
    document_agent: LlmAgent
    preprocessing_agent: LlmAgent
    voice_agent: LlmAgent
    synthesis_agent: LlmAgent
    finalization_agent: LlmAgent
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, name: str = "AudiobookPipeline"):
        """Initialize the pipeline with 5 specialized sub-agents."""
        
        # STAGE 1: Document Intelligence
        # Gemini decides: chapter breaks, dialogue vs narration, metadata filtering
        document_agent = LlmAgent(
            name="DocumentExtractor",
            model=Gemini(model=settings.gemini_text_model),
            instruction="""
You extract and understand document structure.

Use tools to:
1. Extract text from PDF/TXT
2. Get document metadata

Think about:
- Is this a chapter break?
- Should paragraphs be merged?
- Is this dialogue or narration?
- Is this metadata (TOC, headers, footers)?

Store extracted text in output_key for next stage.
""",
            tools=[extract_text_from_txt, extract_text_from_pdf, get_document_metadata],
            output_key="raw_text"
        )
        
        # STAGE 2: Preprocessing Intelligence
        # Gemini decides: garbage text, repeated headers, structural understanding
        preprocessing_agent = LlmAgent(
            name="TextPreprocessor",
            model=Gemini(model=settings.gemini_text_model),
            instruction="""
You clean and segment text intelligently.

Input: {raw_text}

Use tools to:
1. Clean text (fix formatting)
2. Filter unwanted content (copyright, headers)
3. Segment into speech-friendly chunks

Think about:
- Is this garbage text or meaningful content?
- Should this line be removed or kept?
- Where are natural speech breaks?
- Is this a chapter intro vs transition?

Store segments in output_key for next stage.
""",
            tools=[clean_text, filter_unwanted_content, segment_text],
            output_key="text_segments"
        )
        
        # STAGE 3: Voice Planning Intelligence
        # Gemini decides: male/female voice, emotional tone, dialogue style
        voice_agent = LlmAgent(
            name="VoicePlanner",
            model=Gemini(model=settings.gemini_text_model),
            instruction="""
You assign voices intelligently to each segment.

Input segments: {text_segments}

Use tools to:
1. Detect characters in dialogue
2. Analyze text gender/tone
3. Assign appropriate voice profiles

Think about:
- Is this male or female voice?
- Is this dialogue or narration?
- What emotional tone (calm, excited, dramatic)?
- Should speed/prosody change for this section?

Store voice assignments in output_key for next stage.
""",
            tools=[detect_characters, analyze_text_gender, assign_voice_profile],
            output_key="voice_assignments"
        )
        
        # STAGE 4: Synthesis Execution
        # Gemini decides: retry parameters, cloud vs local, error recovery
        synthesis_agent = LlmAgent(
            name="AudioSynthesizer",
            model=Gemini(model=settings.gemini_text_model),
            instruction="""
You synthesize audio for each segment.

Input segments: {text_segments}
Voice assignments: {voice_assignments}

Use tools to:
1. Synthesize audio for EACH segment with use_temp_dir=True (saves to temp directory)
2. Cleanup TTS resources after batch

Think about:
- Should I retry with different parameters if it fails?
- Is this text clean enough for TTS?
- Should I use cloud or local TTS?

CRITICAL: 
- Synthesize ALL segments. Do not skip any.
- ALWAYS use use_temp_dir=True when calling synthesize_audio
- Store all returned audio file paths in session state

Store audio chunk paths in output_key for next stage.
""",
            tools=[synthesize_audio, cleanup_tts_resources],
            output_key="audio_chunks"
        )
        
        # STAGE 5: Finalization Intelligence
        # Gemini decides: crossfade timing, normalization level, quality checks
        finalization_agent = LlmAgent(
            name="AudioFinalizer",
            model=Gemini(model=settings.gemini_text_model),
            instruction="""
You finalize the audiobook with proper naming and cleanup.

Input audio chunks: {audio_chunks}

Use tools to:
1. Merge audio chunks (ffmpeg concat - lossless, fast)
2. Normalize audio levels
3. Export to final format (MP3 recommended)
4. Get final audio info

CRITICAL OUTPUT NAMING:
- Extract input filename from user's original request (e.g., "sample.txt")
- Output file MUST match input name (e.g., sample.txt → sample.mp3)
- Use merge_audio_chunks with cleanup_chunks=True (auto-deletes temp files)
- Use export_audio_format to convert merged.wav → <inputfilename>.mp3
- Temp directory (.temp/) will be automatically removed after cleanup

Think about:
- Are all chunks present?
- Is normalization at good level (-20 dBFS)?
- Is the final quality good?
- Did I name the output file correctly based on input filename?

Store final audiobook path in output_key.
""",
            tools=[merge_audio_chunks, normalize_audio, export_audio_format, get_audio_info],
            output_key="final_audiobook"
        )
        
        # Initialize BaseAgent with sub-agents
        super().__init__(
            name=name,
            document_agent=document_agent,
            preprocessing_agent=preprocessing_agent,
            voice_agent=voice_agent,
            synthesis_agent=synthesis_agent,
            finalization_agent=finalization_agent,
            sub_agents=[
                document_agent,
                preprocessing_agent,
                voice_agent,
                synthesis_agent,
                finalization_agent
            ]
        )
    
    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Deterministic 5-stage pipeline execution.
        
        Each stage is GUARANTEED to run (no LLM skipping).
        Includes error handling and state validation.
        """
        logger.info(f"[{self.name}] Starting audiobook generation pipeline")
        
        # Check GPU status before starting
        gpu_info = get_gpu_info()
        if gpu_info['available']:
            logger.info(
                f"[{self.name}] GPU: {gpu_info['device_name']}, "
                f"Free VRAM: {gpu_info['free_memory_gb']:.2f} GB, "
                f"Utilization: {gpu_info['utilization_percent']:.1f}%"
            )
            if gpu_info['free_memory_gb'] < 2.0:
                logger.warning(
                    f"[{self.name}] ⚠️  Low VRAM ({gpu_info['free_memory_gb']:.2f} GB). "
                    "Consider closing other GPU applications."
                )
        else:
            logger.warning(f"[{self.name}] ⚠️  No GPU detected. Local TTS will be unavailable.")
        
        # ============================================================
        # STAGE 1: DOCUMENT EXTRACTION
        # ============================================================
        logger.info(f"[{self.name}] STAGE 1/5: Document Extraction")
        async for event in self.document_agent.run_async(ctx):
            logger.debug(f"[DocumentExtractor] {event.model_dump_json(indent=2, exclude_none=True)}")
            yield event
        
        # Validate: raw_text must exist
        if "raw_text" not in ctx.session.state or not ctx.session.state["raw_text"]:
            error_msg = "Document extraction failed - no text extracted"
            logger.error(f"[{self.name}] {error_msg}")
            raise ValueError(error_msg)
        
        logger.info(f"[{self.name}] [OK] Extracted {len(ctx.session.state['raw_text'])} characters")
        
        # ============================================================
        # STAGE 2: PREPROCESSING
        # ============================================================
        logger.info(f"[{self.name}] STAGE 2/5: Text Preprocessing")
        async for event in self.preprocessing_agent.run_async(ctx):
            logger.debug(f"[TextPreprocessor] {event.model_dump_json(indent=2, exclude_none=True)}")
            yield event
        
        # Validate: text_segments must exist
        if "text_segments" not in ctx.session.state or not ctx.session.state["text_segments"]:
            error_msg = "Preprocessing failed - no segments created"
            logger.error(f"[{self.name}] {error_msg}")
            raise ValueError(error_msg)
        
        segment_count = len(ctx.session.state["text_segments"])
        logger.info(f"[{self.name}] [OK] Created {segment_count} segments")
        
        # ============================================================
        # STAGE 3: VOICE PLANNING
        # ============================================================
        logger.info(f"[{self.name}] STAGE 3/5: Voice Planning")
        async for event in self.voice_agent.run_async(ctx):
            logger.debug(f"[VoicePlanner] {event.model_dump_json(indent=2, exclude_none=True)}")
            yield event
        
        # Validate: voice_assignments must exist (can be dict or list)
        if "voice_assignments" not in ctx.session.state:
            # Fallback: create default narrator assignment
            logger.warning(f"[{self.name}] No voice_assignments in state, creating default narrator")
            ctx.session.state["voice_assignments"] = {
                "voice_profile": {
                    "name": "narrator",
                    "gender": "neutral",
                    "reference_audio": "./reference_audio/male.wav",
                    "language": "en",
                    "temperature": 0.75,
                    "speed": 1.0,
                    "repetition_penalty": 7.0
                }
            }
        
        logger.info(f"[{self.name}] [OK] Voice assignments completed")
        
        # ============================================================
        # STAGE 4: AUDIO SYNTHESIS (with retry logic)
        # ============================================================
        logger.info(f"[{self.name}] STAGE 4/5: Audio Synthesis")
        
        # Check GPU before synthesis
        gpu_info = get_gpu_info()
        if gpu_info['available']:
            logger.info(
                f"[{self.name}] Pre-synthesis GPU check: "
                f"{gpu_info['free_memory_gb']:.2f} GB free, "
                f"{gpu_info['utilization_percent']:.1f}% utilized"
            )
            if gpu_info['free_memory_gb'] < 1.5:
                logger.warning(
                    f"[{self.name}] ⚠️  CRITICAL: Only {gpu_info['free_memory_gb']:.2f} GB VRAM free. "
                    "Synthesis may fail or be very slow."
                )
        
        max_retries = 3
        synthesis_success = False
        
        for attempt in range(max_retries):
            try:
                async for event in self.synthesis_agent.run_async(ctx):
                    logger.debug(f"[AudioSynthesizer] {event.model_dump_json(indent=2, exclude_none=True)}")
                    yield event
                
                # Validate: audio_chunks must exist
                if "audio_chunks" in ctx.session.state and ctx.session.state["audio_chunks"]:
                    synthesis_success = True
                    break
                else:
                    raise ValueError("No audio chunks generated")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"[{self.name}] Synthesis attempt {attempt + 1} failed: {e}. Retrying...")
                else:
                    logger.error(f"[{self.name}] Synthesis failed after {max_retries} attempts")
                    raise
        
        if not synthesis_success:
            raise ValueError("Audio synthesis failed - no chunks generated")
        
        chunk_count = len(ctx.session.state["audio_chunks"])
        logger.info(f"[{self.name}] [OK] Synthesized {chunk_count} audio chunks")
        
        # GPU cleanup after synthesis
        gpu_info = get_gpu_info()
        if gpu_info['available']:
            logger.info(
                f"[{self.name}] Post-synthesis GPU: "
                f"{gpu_info['allocated_memory_gb']:.2f} GB allocated, "
                f"{gpu_info['free_memory_gb']:.2f} GB free"
            )
        
        # ============================================================
        # STAGE 5: FINALIZATION
        # ============================================================
        logger.info(f"[{self.name}] STAGE 5/5: Finalization")
        async for event in self.finalization_agent.run_async(ctx):
            logger.debug(f"[AudioFinalizer] {event.model_dump_json(indent=2, exclude_none=True)}")
            yield event
        
        # Validate: final_audiobook must exist
        if "final_audiobook" not in ctx.session.state or not ctx.session.state["final_audiobook"]:
            error_msg = "Finalization failed - no final audiobook created"
            logger.error(f"[{self.name}] {error_msg}")
            raise ValueError(error_msg)
        
        final_path = ctx.session.state['final_audiobook']
        logger.info(f"[{self.name}] [DONE] Pipeline complete: {final_path}")
        
        # Final GPU status
        gpu_info = get_gpu_info()
        if gpu_info['available']:
            logger.info(
                f"[{self.name}] Final GPU state: "
                f"{gpu_info['allocated_memory_gb']:.2f} GB allocated, "
                f"{gpu_info['free_memory_gb']:.2f} GB free, "
                f"{gpu_info['utilization_percent']:.1f}% utilization"
            )


# Export the root agent for CLI/Runner usage
root_agent = AudiobookPipelineAgent(name="AudiobookPipeline")

