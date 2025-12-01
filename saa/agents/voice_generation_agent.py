"""
Voice Generation Agent - Stage 3 of audiobook pipeline (ADK LlmAgent)
Generates audio for each chunk using Gemini-guided TTS synthesis
"""
from google.adk.agents import LlmAgent

from saa.models import get_model_provider
from saa.config import get_settings
from saa.tools.resume_tools import synthesize_remaining_chunks
import json
from pathlib import Path
from typing import Dict, Any

settings = get_settings()


def create_voice_generation_agent(job_state_path: str = None) -> LlmAgent:
    """
    Create ADK-based Voice Generation Agent.
    
    Stage 3: Voice Synthesis
    - Reads chunks.json from staging
    - Synthesizes audio for each chunk
    - Handles Replicate/local TTS fallback
    - Saves to .temp/voices/chunk_<id>.wav
    
    Args:
        job_state_path: Optional path to JobState JSON for checkpoint tracking
    
    GEMINI INTELLIGENCE - TTS Orchestration Decisions:
    =================================================
    
    1. Retry Strategy for Failed Synthesis:
       DECISION: "Why did synthesis fail and how should I retry?"
       
       Scenario A: "Text too complex for TTS"
       - Original: "The xylophonist's quixotic performance..."
       - AI rewrites: "The musician's unusual performance..."
       - Retry with simplified text
       
       Scenario B: "API rate limit hit"
       - Wait 2 seconds, retry with same parameters
       - If fails again, fall back to local TTS
       
       Scenario C: "Text has special characters"
       - Clean: "Price: $19.99" → "Price: nineteen ninety-nine"
       - Retry with cleaned text
       
       WHY AI?: Diagnosis requires understanding error context
    
    2. Cloud vs Local TTS Decision:
       DECISION: "Which TTS provider should I use for this chunk?"
       
       Use Replicate (cloud) when:
       - ✅ API token available
       - ✅ Text is standard (no special requirements)
       - ✅ Speed more important than cost
       
       Use Local XTTS when:
       - ✅ Replicate failed (fallback)
       - ✅ GPU available locally
       - ✅ Privacy required (sensitive text)
       
       WHY AI?: Adaptive provider selection based on context
    
    3. Error Recovery - Text Rewriting:
       DECISION: "Can I rewrite this text to work with TTS?"
       
       Problematic: "He said, 'I can't—no, I won't—do that.'"
       - TTS chokes on nested punctuation
       
       AI rewrites: "He said he couldn't and wouldn't do that."
       - Preserves meaning, TTS-friendly format
       
       WHY AI?: Semantic-preserving rewrites, not just regex
    
    4. Quality Settings Optimization:
       DECISION: "What synthesis parameters produce best quality?"
       
       For emotional speech:
       - temperature=0.85 (more expressive)
       - speed=1.1 (slightly faster for excitement)
       
       For technical content:
       - temperature=0.65 (more consistent)
       - speed=0.9 (slower for clarity)
       
       WHY AI?: Context-aware parameter tuning
    
    5. GPU Resource Management:
       DECISION: "When should I free GPU memory?"
       
       After every N chunks (N=10):
       - Call cleanup_tts_resources
       - Prevents GPU OOM errors
       
       After synthesis errors:
       - Immediate cleanup before retry
       - Frees memory for fresh attempt
       
       WHY AI?: Predictive resource management
    
    CRITICAL IMPLEMENTATION NOTE:
    ============================
    The instruction explicitly tells Gemini to:
    - CALL synthesize_audio for EACH chunk (not describe, actually call!)
    - MAP voice names to reference_audio files
    - VERIFY tool responses (check status field)
    - HANDLE errors gracefully (retry, rewrite, skip)
    
    Without this explicit instruction, LLM might:
    - Describe what it WOULD do instead of doing it
    - Skip chunks (optimization gone wrong)
    - Hallucinate file paths
    
    Returns:
        LlmAgent configured for intelligent TTS synthesis
    """
    
    # Include checkpoint instruction if state path provided
    checkpoint_instruction = ""
    if job_state_path:
        checkpoint_instruction = f"""

## CHECKPOINT TRACKING (RESUME SUPPORT):
**State Path**: {job_state_path}

When calling synthesize_audio, you MUST include these parameters for checkpoint tracking:
- chunk_id={"{"}chunk["id"]{"}"}  # The chunk ID number from chunks.json
- job_state_path="{job_state_path}"  # Path to state file

Example:
```python
synthesize_audio(
  text=chunk["text"],
  output_path="chunk_0003.wav",
  reference_audio="reference_audio/male.wav",
  chunk_id=3,  # CRITICAL: Pass the chunk ID!
  job_state_path="{job_state_path}"  # CRITICAL: Pass the state path!
)
```

This allows users to resume from interruptions - the system tracks which chunks are complete!
"""
    
    return LlmAgent(
        name="VoiceGenerationAgent",
        model=get_model_provider(),  # Auto-selects provider from env (Gemini/Ollama/OpenRouter)
        tools=[synthesize_remaining_chunks],
        instruction=f"""
You are a voice synthesis agent. Your job is simple:

**CALL THIS ONE TOOL:**
synthesize_remaining_chunks(job_state_path="{job_state_path or ''}")

That's it! This tool does EVERYTHING for you:
- Checks state.json to see which chunks are already done
- Reads chunks.json to get all chunks  
- Synthesizes ONLY the chunks that aren't complete yet
- Updates state after each chunk
- Returns a summary

**You just call the tool and report the result.**

Example:
    result = synthesize_remaining_chunks(job_state_path="{job_state_path or ''}")
    
    if result["status"] == "success":
        print(f"Synthesized chunks_synthesized chunks")
        print(f"Skipped chunks_skipped already complete")
    else:
        print(f"Error: error")

The tool handles ALL the complexity - you just call it and report!
"""
    )
