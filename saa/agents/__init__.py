"""
Audiobook Pipeline Agents

New Architecture (5-Stage ADK Agents):
- ExtractionAgent: Extract text from PDF/TXT
- StagingAgent: Clean, chunk, add voice metadata  
- VoiceGenerationAgent: Synthesize audio chunks
- MergeAgent: Merge and export final audiobook
- CleanupAgent: Clean up temp files

Orchestrator: Coordinates all 5 agents with intelligent LlmAgent coordinator
"""
from saa.agents.extraction_agent import create_extraction_agent
from saa.agents.staging_agent import create_staging_agent
from saa.agents.voice_generation_agent import create_voice_generation_agent
from saa.agents.merge_agent import create_merge_agent
from saa.agents.cleanup_agent import create_cleanup_agent
from saa.agents.orchestrator import AudiobookOrchestrator, run_audiobook_generation

__all__ = [
    # ADK agent factories
    "create_extraction_agent",
    "create_staging_agent",
    "create_voice_generation_agent",
    "create_merge_agent",
    "create_cleanup_agent",
    # Orchestrator
    "AudiobookOrchestrator",
    "run_audiobook_generation",
]

