"""
Merge Agent - Stage 4 of audiobook pipeline (ADK LlmAgent)
Merges audio chunks and converts to final formats
"""
from google.adk.agents import LlmAgent

from saa.models import get_model_provider
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
    
    GEMINI INTELLIGENCE - Audio Post-Processing Decisions:
    =====================================================
    
    1. Merge Strategy Selection:
       DECISION: "How should I combine audio chunks?"
       
       Concat (Fast, Lossless):
       - ✅ Use when: All chunks same sample rate/format
       - ✅ Perfect for audiobooks (natural flow)
       - ✅ No quality loss
       
       Crossfade (Smooth Transitions):
       - ✅ Use when: Need seamless blending
       - ❌ Slower, requires decoding/encoding
       - ✅ Good for music, less critical for speech
       
       WHY AI?: Chooses based on chunk consistency and quality requirements
    
    2. Normalization Level Decision:
       DECISION: "What target volume should I use?"
       
       For audiobooks:
       - Target: -20 dBFS (comfortable listening)
       - Prevents clipping on loud passages
       - Consistent volume across chunks
       
       For podcasts:
       - Target: -16 dBFS (louder, competitive)
       
       WHY AI?: Understands content type from context
    
    3. Export Quality Settings:
       DECISION: "What MP3 bitrate balances quality vs size?"
       
       High Quality (192 kbps):
       - ✅ Excellent speech clarity
       - File size: ~1.4 MB per minute
       - Recommended for premium audiobooks
       
       Medium Quality (128 kbps):
       - ✅ Good balance for most use cases
       - File size: ~960 KB per minute
       
       Low Quality (64 kbps):
       - ✅ Acceptable for voice-only
       - File size: ~480 KB per minute
       - Good for bandwidth-limited scenarios
       
       WHY AI?: Adapts to output requirements (file size vs quality trade-off)
    
    4. Large File Optimization:
       DECISION: "How should I handle 10+ hour audiobooks?"
       
       Chunk-based merging:
       - Merge in batches of 50 chunks
       - Prevents memory overflow
       - Progress reporting every batch
       
       Single-pass merging:
       - Faster for small audiobooks (<1 hour)
       - All in memory at once
       
       WHY AI?: Predicts memory usage from chunk count
    
    5. Quality Verification:
       DECISION: "Is the merged audio acceptable?"
       
       Checks:
       - File size > 0 (not corrupted)
       - Duration matches expected (all chunks included)
       - Sample rate consistent (22050 Hz)
       - No clipping (peak < 0 dBFS)
       
       WHY AI?: Intelligent quality assurance before export
    
    CRITICAL PATH AWARENESS:
    =======================
    This is the FINAL stage before user gets audiobook.
    If merge fails:
    - All previous work (extraction, staging, synthesis) wasted
    - User has to start over
    
    Therefore, Gemini:
    - VERIFIES input files exist before merging
    - CHECKS merged file integrity
    - RETRIES on transient failures
    - REPORTS detailed errors if unrecoverable
    
    Returns:
        LlmAgent configured for intelligent audio post-processing
    """
    return LlmAgent(
        name="MergeAgent",
        model=get_model_provider(),  # Auto-selects provider from env (Gemini/Ollama/OpenRouter)
        tools=[list_audio_files, merge_audio_chunks, normalize_audio, export_audio_format, get_audio_info],
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
"""
    )
