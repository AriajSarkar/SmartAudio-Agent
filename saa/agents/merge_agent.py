"""
Merge Agent - Stage 4 of audiobook pipeline (ADK LlmAgent)
Merges audio chunks and converts to final formats
"""
from google.adk.agents import LlmAgent
from google.adk.models import Gemini

from saa.config import get_settings
from saa.tools.audio_tools import merge_audio_chunks, normalize_audio, export_audio_format, get_audio_info
from pathlib import Path
from typing import Dict, Any

settings = get_settings()


def list_audio_files(directory: str) -> Dict[str, Any]:
    """
    List all WAV files in a directory.
    
    Args:
        directory: Path to directory to scan
        
    Returns:
        Dictionary with status and list of WAV files
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return {
                "status": "error",
                "error": f"Directory not found: {directory}"
            }
        
        wav_files = sorted([str(dir_path / f.name) for f in dir_path.glob("*.wav")])
        
        return {
            "status": "success",
            "files": wav_files,
            "count": len(wav_files),
            "directory": str(dir_path.absolute())
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }



def create_merge_agent() -> LlmAgent:
    """
    Create ADK-based Merge Agent.
    
    Stage 4: Audio Merging & Export
    - Merges all .temp/voices/*.wav files
    - Normalizes audio levels
    - Exports to final formats (WAV + MP3)
    - Saves to output/<job_id>/
    
    Gemini Intelligence:
    - Decides merge strategy (concat vs crossfade)
    - Chooses normalization levels
    - Adjusts export quality settings
    - Handles large file optimization
    
    Returns:
        LlmAgent configured for audio merging
    """
    return LlmAgent(
        name="MergeAgent",
        model=Gemini(model=settings.gemini_text_model),
        instruction="""
You are an intelligent audio merging agent. You MUST actually merge audio files.

## CRITICAL - Your Required Actions:
1. List all WAV files in output/.temp/voices/
2. Merge them in order using merge_audio_chunks tool
3. Export to output/<job_id>/final.wav
4. Convert to output/<job_id>/final.mp3
5. Report final file details

## Tools Available:
1. **list_audio_files** - List WAV files in directory (CALL THIS FIRST!)
2. **merge_audio_chunks** - Merge WAV files (YOU MUST CALL THIS!)
3. **normalize_audio** - Adjust volume levels
4. **export_audio_format** - Convert to MP3
5. **get_audio_info** - Inspect audio properties

## Step-by-Step Workflow:
1. **CALL list_audio_files("output/.temp/voices")**  
   - This gives you the list of chunk_XXXX.wav files
2. Extract the list of files from the tool response
3. **CALL merge_audio_chunks** with these parameters:
   - input_files=[list of WAV file paths from step 1]
   - output_path="<job_id>/final.wav"  # NO 'output/' prefix! Just job_id/final.wav
   - method="concat"  # Fast, lossless concatenation
4. **CALL export_audio_format** to convert to MP3:
   - input_file="<job_id>/final.wav"  # NO 'output/' prefix!
   - output_file="<job_id>/final.mp3"  # NO 'output/' prefix!
   - format="mp3"
   - quality="high"
   - cleanup_input=False  # Keep both WAV and MP3
5. Report: "Merged N chunks into final.wav (X MB) and final.mp3 (Y MB)"

NOTE: The coordinator will provide the job_id. Use it in output paths WITHOUT 'output/' prefix.
""",
        tools=[list_audio_files, merge_audio_chunks, normalize_audio, export_audio_format, get_audio_info]
    )
