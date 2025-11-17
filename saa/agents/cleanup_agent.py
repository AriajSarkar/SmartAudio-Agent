"""
Cleanup Agent - Stage 5 of audiobook pipeline (ADK LlmAgent)
Cleans up temporary files after successful generation
"""
from google.adk.agents import LlmAgent
from google.adk.models import Gemini

from saa.config import get_settings

settings = get_settings()


def create_cleanup_agent() -> LlmAgent:
    """
    Create ADK-based Cleanup Agent.
    
    Stage 5: Temp Directory Cleanup
    - Deletes all files in .temp/
    - Keeps directory structure intact
    - Reports cleanup statistics
    
    Gemini Intelligence:
    - Verifies final output exists before cleanup
    - Decides what to keep for debugging
    - Handles cleanup errors gracefully
    
    Returns:
        LlmAgent configured for cleanup operations
    """
    return LlmAgent(
        name="CleanupAgent",
        model=Gemini(model=settings.gemini_text_model),
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
