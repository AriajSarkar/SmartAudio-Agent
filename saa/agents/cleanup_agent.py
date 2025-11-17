"""
Cleanup Agent - Stage 5 of audiobook pipeline (ADK LlmAgent)
Cleans up temporary files after successful generation
"""
from google.adk.agents import LlmAgent

from saa.models import get_model_provider
from saa.config import get_settings

settings = get_settings()


def create_cleanup_agent() -> LlmAgent:
    """
    Create ADK-based Cleanup Agent.
    
    Stage 5: Temp Directory Cleanup
    - Deletes all files in .temp/
    - Keeps directory structure intact
    - Reports cleanup statistics
    
    GEMINI INTELLIGENCE - Cleanup Strategy Decisions:
    ================================================
    
    1. Safety Verification Before Cleanup:
       DECISION: "Is it safe to delete temp files?"
       
       Verify FIRST:
       - ✅ Final audiobook exists (output/<job_id>/final.mp3)
       - ✅ File size > 0 (not corrupted)
       - ✅ File is accessible (not locked)
       
       If ANY check fails:
       - ❌ DO NOT delete temp files
       - ❌ Preserve for debugging
       - ❌ Report what's wrong
       
       WHY AI?: Prevents accidental data loss from failed generations
    
    2. Selective Preservation for Debugging:
       DECISION: "Should I keep some temp files?"
       
       Keep when:
       - Warnings occurred (keep chunks.json to inspect)
       - Synthesis had retries (keep failed chunk text)
       - User requested debug mode (keep everything)
       
       Delete when:
       - Clean successful run (no warnings/errors)
       - User confirmed cleanup (explicit flag)
       
       WHY AI?: Context-aware cleanup (debugging vs production)
    
    3. Error Recovery During Cleanup:
       DECISION: "What if cleanup itself fails?"
       
       Scenario A: File locked by another process
       - Retry after 1 second
       - If still locked, skip and log warning
       - Don't fail entire pipeline
       
       Scenario B: Permission denied
       - Log error with file path
       - Continue with other files
       - Report partial cleanup
       
       WHY AI?: Graceful degradation (cleanup is non-critical)
    
    4. Cleanup Order Optimization:
       DECISION: "What order minimizes issues?"
       
       Delete order:
       1. .temp/voices/*.wav (largest files first - free space)
       2. .temp/staged/chunks.json (intermediate data)
       3. .temp/extracted/extracted.txt (source data)
       
       Keep directory structure:
       - .temp/ folder remains
       - .temp/extracted/ folder remains
       - .temp/staged/ folder remains
       - .temp/voices/ folder remains
       
       WHY AI?: Optimizes disk I/O and maintains workspace structure
    
    5. Reporting Statistics:
       DECISION: "What cleanup metrics matter to user?"
       
       Report:
       - Files deleted count (transparency)
       - Disk space freed in MB (satisfaction)
       - Any errors encountered (transparency)
       - Preserved files if debugging (actionability)
       
       Don't report:
       - Individual file names (too verbose)
       - Timestamps (not relevant)
       
       WHY AI?: User-centric reporting (what they care about)
    
    ARCHITECTURAL NOTE: Why This Agent Exists
    =========================================
    Could we just delete temp files in orchestrator? YES.
    
    But having dedicated agent provides:
    - ✅ Explicit verification step (safety)
    - ✅ Intelligent error handling (graceful degradation)
    - ✅ Clean separation of concerns (single responsibility)
    - ✅ Observable step in pipeline (debugging)
    
    Cleanup failures DON'T fail the pipeline:
    - Audiobook generation succeeded
    - User has final output
    - Temp files are just disk clutter (not critical)
    
    Returns:
        LlmAgent configured for intelligent, safe cleanup
    """
    return LlmAgent(
        name="CleanupAgent",
        model=get_model_provider(),  # Auto-selects provider from env (Gemini/Ollama/OpenRouter)
        instruction="""
You are an intelligent cleanup agent.

Your task is to clean up temporary files after successful audiobook generation.

## Input:
You will receive final audiobook info from the coordinator after all stages complete.

## Tools Available:
No tools needed - you provide cleanup instructions.

## Your Intelligence:
Think about cleanup strategy:
- Is the final audiobook successfully created?
- Should I keep temp files for debugging?
- Are there any errors that need investigation?
- Can I safely delete all temp files?

## Workflow:
1. Verify final output exists:
   - Check `output/<job_id>/final.mp3` exists
   - Confirm file size > 0
2. If successful:
   - Delete all files in `.temp/extracted/`
   - Delete all files in `.temp/staged/`
   - Delete all files in `.temp/voices/`
   - Keep directory structure intact
3. If errors occurred:
   - Keep temp files for debugging
   - Log which files were preserved
4. Report cleanup statistics

## Output:
Store cleanup results in **output_key** (pipeline complete).

Provide a summary of:
- Files deleted count
- Disk space freed
- Temp directories status
- Any files preserved for debugging
""",
        tools=[]  # No tools needed - cleanup is handled by orchestrator
    )
