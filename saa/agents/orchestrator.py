"""
Audiobook Pipeline Orchestrator
Coordinates the 5-stage ADK agent pipeline with SequentialAgent
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool

from saa.models import get_model_provider
from saa.agents.extraction_agent import create_extraction_agent
from saa.agents.staging_agent import create_staging_agent
from saa.agents.refinement_agent import create_refinement_agent
from saa.agents.voice_generation_agent import create_voice_generation_agent
from saa.agents.merge_agent import create_merge_agent
from saa.agents.cleanup_agent import create_cleanup_agent
from saa.utils.workspace import WorkspaceManager
from saa.utils import setup_logger
from saa.config import get_settings

logger = setup_logger(
    name="orchestrator",
    level=logging.INFO,
    log_file="logs/orchestrator.log"
)


class AudiobookOrchestrator:
    """
    Orchestrates the 5-stage audiobook generation pipeline using ADK agents.
    
    Pipeline Flow:
        1. ExtractionAgent      → Extract text from PDF/TXT
        2. StagingAgent         → Clean, chunk, add voice metadata
        2.5 TextRefinementAgent → Refine chunks (remove dashes, artifacts)
        3. VoiceGenerationAgent → Synthesize audio chunks
        4. MergeAgent           → Merge and export final audiobook
        5. CleanupAgent         → Clean up temp files
    
    ARCHITECTURE DECISION: AgentTool Coordinator Pattern
    ====================================================
    We use a Gemini-powered coordinator that calls sub-agents as tools.
    
    Why NOT SequentialAgent?
    ------------------------
    Initial implementation used SequentialAgent, which had critical flaws:
    - ❌ LLM-based routing SKIPPED VoiceGenerationAgent entirely (unpredictable)
    - ❌ output_key state passing caused hallucinations (LLM invented non-existent keys)
    - ❌ No explicit file verification between stages
    - ❌ Poor error handling and debugging
    
    Why AgentTool Coordinator?
    --------------------------
    Current implementation uses coordinator + file verification:
    - ✅ Gemini DECIDES when to call each agent (intelligent orchestration)
    - ✅ File-based coordination (verify_stage_output checks actual files)
    - ✅ Explicit error handling (report_stage_error for debugging)
    - ✅ Clear progress communication to user
    - ✅ No hallucinations (files either exist or don't)
    
    Gemini Intelligence:
    -------------------
    The coordinator uses Gemini 2.5 Flash to:
    - Understand pipeline state (which stages completed)
    - Decide next action based on file verification
    - Handle errors intelligently (retry, skip, report)
    - Communicate progress clearly to user
    
    WHY AI? (Why Gemini Orchestration Matters):
    -------------------------------------------
    Without Gemini coordination, you'd need:
    - Hardcoded pipeline logic (brittle, no adaptability)
    - Manual error handling for every edge case
    - No intelligent recovery from failures
    
    With Gemini intelligence:
    - Adaptive workflow (handles unexpected situations)
    - Smart error recovery (decides when to retry vs abort)
    - User-friendly progress reporting
    """
    
    def __init__(
        self,
        input_file: Path,
        output_dir: Path = Path("./output"),
        job_id: Optional[str] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            input_file: Path to PDF or TXT file
            output_dir: Base output directory
            job_id: Unique job identifier (auto-generated if None)
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.job_id = job_id or f"job_{uuid.uuid4().hex[:8]}"
        
        # Setup workspace
        self.workspace = WorkspaceManager(base_path=output_dir)
        self.workspace.setup()
        
        # Create job output directory
        self.job_output_dir = output_dir / self.job_id
        self.job_output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[Orchestrator] Initialized for job: {self.job_id}")
        logger.info(f"[Orchestrator] Input: {input_file}")
        logger.info(f"[Orchestrator] Output: {self.job_output_dir}")
    
    def _create_debug_tool(self):
        """Create debugging tool for AI to report issues."""
        def report_stage_error(stage_name: str, reason: str, expected: str, actual: str) -> Dict[str, Any]:
            """
            Report when a pipeline stage didn't work as expected.
            
            Call this tool when:
            - Tool returns unexpected result format
            - Expected files not created
            - Stage should proceed to next but can't
            - Need to understand why stage failed
            
            Args:
                stage_name: Which stage failed (ExtractionAgent, StagingAgent, etc.)
                reason: Why you think it failed
                expected: What you expected to happen
                actual: What actually happened
            
            Returns:
                Debugging guidance and next steps
            """
            logger.error(f"[DEBUG] Stage '{stage_name}' failed")
            logger.error(f"[DEBUG] Reason: {reason}")
            logger.error(f"[DEBUG] Expected: {expected}")
            logger.error(f"[DEBUG] Actual: {actual}")
            
            return {
                "status": "debug_reported",
                "stage": stage_name,
                "guidance": f"Stage '{stage_name}' encountered issues. Check tool return format and file existence.",
                "next_steps": "Review tool documentation, verify file paths, check temp directory structure"
            }
        
        return report_stage_error
    
    def _create_verification_tool(self):
        """Create tool for AI to verify stage completion."""
        def verify_stage_output(stage_name: str, expected_path: str) -> Dict[str, Any]:
            """
            Verify that a pipeline stage produced expected output.
            
            Args:
                stage_name: Stage that just completed
                expected_path: Path to file that should exist
            
            Returns:
                Verification result with file details
            """
            path = Path(expected_path)
            exists = path.exists()
            
            result = {
                "status": "verified" if exists else "missing",
                "stage": stage_name,
                "path": str(path),
                "exists": exists
            }
            
            if exists:
                result["size_bytes"] = path.stat().st_size
                logger.info(f"[VERIFY] OK - {stage_name} output exists: {path}")
            else:
                logger.warning(f"[VERIFY] MISSING - {stage_name} output missing: {path}")
            
            return result
        
        return verify_stage_output
    
    def create_pipeline(self) -> LlmAgent:
        """
        Create intelligent coordinator agent with 5 sub-agents as tools.
        
        Returns:
            LlmAgent that coordinates pipeline with Gemini intelligence
        """
        logger.info("[Orchestrator] Building intelligent agent pipeline...")
        settings = get_settings()
        
        # Import provider function
        from saa.models import get_model_provider as _get_provider
        
        # Create all agents (now 6 stages)
        extraction_agent = create_extraction_agent()
        staging_agent = create_staging_agent()
        refinement_agent = create_refinement_agent()  # NEW: Stage 2.5
        voice_generation_agent = create_voice_generation_agent()
        merge_agent = create_merge_agent()
        cleanup_agent = create_cleanup_agent()
        
        # Wrap agents as callable tools
        extraction_tool = AgentTool(extraction_agent)
        staging_tool = AgentTool(staging_agent)
        refinement_tool = AgentTool(refinement_agent)  # NEW: Stage 2.5
        voice_tool = AgentTool(voice_generation_agent)
        merge_tool = AgentTool(merge_agent)
        cleanup_tool = AgentTool(cleanup_agent)
        
        # Create debugging tools
        debug_tool = self._create_debug_tool()
        verify_tool = self._create_verification_tool()
        
        # Create intelligent coordinator
        coordinator = LlmAgent(
            name="PipelineCoordinator",
            model=_get_provider(),  # Auto-selects provider from env (Gemini/Ollama/OpenRouter)
            instruction=f"""
You are an intelligent audiobook pipeline coordinator. Your job is to orchestrate 5 stages in EXACT ORDER:

**CRITICAL WORKFLOW:**
1. Call ExtractionAgent
   - The agent will extract text and save to output/.temp/extracted/extracted.txt
   - After agent completes, call verify_stage_output("ExtractionAgent", "output/.temp/extracted/extracted.txt")
   - If file exists: Say "OK - Stage 1 complete. Proceeding to staging..."
   - If file missing: Call report_stage_error with details

2. Call StagingAgent
   - The agent will create chunks and save to output/.temp/staged/chunks.json
   - After agent completes, call verify_stage_output("StagingAgent", "output/.temp/staged/chunks.json")
   - If file exists: Say "OK - Stage 2 complete. Proceeding to refinement..."
   - If file missing: Call report_stage_error with details

2.5 Call TextRefinementAgent
   - The agent will refine text chunks (remove dashes, artifacts) in chunks.json
   - After agent completes, call verify_stage_output("TextRefinementAgent", "output/.temp/staged/chunks.json")
   - If file exists: Say "OK - Stage 2.5 complete. Text refined. Proceeding to synthesis..."
   - If file missing: Call report_stage_error with details

3. Call VoiceGenerationAgent
   - The agent will synthesize audio chunks and save to output/.temp/voices/chunk_XXXX.wav
   - After agent completes, call verify_stage_output("VoiceGenerationAgent", "output/.temp/voices")
   - Expect multiple WAV files in voices directory
   - If files exist: Say "OK - Stage 3 complete. Audio synthesized. Proceeding to merge..."
   - If files missing: Call report_stage_error with details

4. Call MergeAgent with message: "Merge audio chunks for job_id: {self.job_id}"
   - The agent will merge audio files and save to output/{self.job_id}/final.wav and final.mp3
   - After agent completes, call verify_stage_output("MergeAgent", "output/{self.job_id}/final.wav")
   - If file exists: Say "OK - Stage 4 complete. Audiobook merged. Proceeding to cleanup..."
   - If file missing: Call report_stage_error with details

5. Call CleanupAgent
   - The agent will clean temporary files
   - After agent completes, say "OK - Stage 5 complete. Pipeline finished!"

**ERROR HANDLING:**
- If ANY verify_stage_output returns {{exists: false}}, STOP pipeline immediately
- Call report_stage_error with stage name and expected file path
- Do NOT proceed to next stage if verification fails

**Your Role:**
- Execute stages in ORDER (1->2->3->4->5)
- VERIFY outputs after each stage
- COMMUNICATE progress clearly
- HANDLE errors intelligently

Input file: {self.input_file}
Job ID: {self.job_id}
Output: {self.job_output_dir}
""",
            tools=[
                extraction_tool,
                staging_tool,
                refinement_tool,  # NEW: Stage 2.5
                voice_tool,
                merge_tool,
                cleanup_tool,
                verify_tool,
                debug_tool
            ]
        )
        
        logger.info("[Orchestrator] OK - Intelligent coordinator created with 5 agents + 2 debug tools")
        return coordinator
    
    async def run_async(self) -> Dict[str, Any]:
        """
        Run the complete audiobook generation pipeline asynchronously.
        
        Returns:
            Dictionary with:
                - status: "success" or "error"
                - job_id: Unique job identifier
                - output_files: List of generated files
                - error: Error message if failed
        """
        logger.info(f"[Orchestrator] Starting pipeline execution...")
        
        try:
            # Create pipeline
            pipeline = self.create_pipeline()
            
            # Create ADK runner with correct app_name
            runner = InMemoryRunner(
                agent=pipeline,
                app_name="saa"  # FIX: Matches agents folder structure
            )
            
            # Prepare initial prompt with clear instructions
            prompt = f"""
Generate audiobook from: {self.input_file}

Execute the 5-stage pipeline:
1. Extract text from file
2. Clean and chunk into segments with voice metadata
3. Synthesize audio for each chunk
4. Merge chunks into final audiobook
5. Clean up temp files

Report progress after each stage. Verify outputs exist. Handle errors gracefully.
"""
            
            logger.info(f"[Orchestrator] Executing intelligent pipeline...")
            
            # Run pipeline with Gemini coordination
            response = await runner.run_debug(prompt)
            
            # Check results
            output_files = self._collect_output_files()
            
            logger.info(f"[Orchestrator] OK - Pipeline complete!")
            logger.info(f"[Orchestrator] Generated {len(output_files)} files")
            
            return {
                "status": "success",
                "job_id": self.job_id,
                "output_files": [str(f) for f in output_files],
                "output_dir": str(self.job_output_dir),
                "error": None
            }
        
        except Exception as e:
            logger.error(f"[Orchestrator] ERROR - Pipeline failed: {str(e)}")
            return {
                "status": "error",
                "job_id": self.job_id,
                "output_files": [],
                "output_dir": str(self.job_output_dir),
                "error": str(e)
            }
    
    def run(self) -> Dict[str, Any]:
        """
        Run the pipeline synchronously (wrapper for async).
        
        Returns:
            Pipeline execution results
        """
        return asyncio.run(self.run_async())
    
    def _collect_output_files(self) -> list[Path]:
        """Collect all generated output files."""
        output_files = []
        
        # Check job output directory
        if self.job_output_dir.exists():
            output_files.extend(self.job_output_dir.glob("final.*"))
        
        return output_files
    
    def cleanup_temp(self):
        """Manually trigger temp cleanup."""
        self.workspace.cleanup()
        logger.info("[Orchestrator] Manual cleanup complete")


# Convenience function for CLI
async def run_audiobook_generation(
    input_file: str,
    output_dir: str = "./output",
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to run audiobook generation.
    
    Args:
        input_file: Path to PDF or TXT file
        output_dir: Output directory
        job_id: Optional job identifier
    
    Returns:
        Generation results dictionary
    """
    orchestrator = AudiobookOrchestrator(
        input_file=Path(input_file),
        output_dir=Path(output_dir),
        job_id=job_id
    )
    
    return await orchestrator.run_async()
