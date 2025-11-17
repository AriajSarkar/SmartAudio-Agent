"""
Voice Generation Agent - Stage 3 of audiobook pipeline (ADK LlmAgent)
Generates audio for each chunk using Gemini-guided TTS synthesis
"""
from google.adk.agents import LlmAgent
from google.adk.models import Gemini

from saa.config import get_settings
from saa.tools.tts_tools import synthesize_audio, cleanup_tts_resources
import json
from pathlib import Path
from typing import Dict, Any

settings = get_settings()


def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse a JSON file.
    
    Args:
        file_path: Path to JSON file to read
        
    Returns:
        Dictionary with status and parsed JSON data
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {
                "status": "error",
                "error": f"File not found: {file_path}"
            }
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "status": "success",
            "data": data,
            "file_path": str(path.absolute())
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def create_voice_generation_agent() -> LlmAgent:
    """
    Create ADK-based Voice Generation Agent.
    
    Stage 3: Voice Synthesis
    - Reads chunks.json from staging
    - Synthesizes audio for each chunk
    - Handles Replicate/local TTS fallback
    - Saves to .temp/voices/chunk_<id>.wav
    
    Gemini Intelligence:
    - Decides retry parameters for failed synthesis
    - Chooses cloud vs local TTS strategy
    - Handles error recovery (text rewriting)
    - Optimizes synthesis quality settings
    - Manages GPU resources
    
    Returns:
        LlmAgent configured for voice synthesis
    """
    return LlmAgent(
        name="VoiceGenerationAgent",
        model=Gemini(model=settings.gemini_text_model),
        instruction="""
You are an intelligent voice synthesis agent. You MUST actually synthesize audio files.

## CRITICAL - Your Required Actions:
1. Read chunks.json from: output/.temp/staged/chunks.json
2. For EACH chunk in the JSON array, call synthesize_audio tool
3. Save audio files to output/.temp/voices/chunk_XXXX.wav
4. After all chunks, call cleanup_tts_resources

## Tools Available:
1. **synthesize_audio** - Generate audio (YOU MUST CALL THIS for each chunk!)
2. **cleanup_tts_resources** - Free GPU memory after synthesis

## Voice to Reference Audio Mapping:
Map chunk voice names to reference audio files:
- "neutral" → "reference_audio/male.wav"  
- "male" → "reference_audio/male.wav"
- "female" → "reference_audio/female.wav"
- "narrator" → "reference_audio/male.wav"

**CRITICAL**: Always provide full path to reference_audio when calling synthesize_audio!

## Step-by-Step Workflow:
1. Read chunks.json from output/.temp/staged/chunks.json  
2. Parse the JSON to get array of chunks
3. For each chunk in the array:
   a. Extract: chunk["id"], chunk["text"], chunk["voice"], chunk["speed"]
   b. Map voice name to reference_audio path (see mapping above)
   c. **CALL synthesize_audio tool** with these parameters:
      - text=chunk["text"]
      - output_path=f"voices/chunk_{chunk['id']:04d}.wav"  # Will be saved to output/.temp/voices/
      - reference_audio="reference_audio/male.wav" (or appropriate mapping)
      - voice=chunk["voice"]
      - speed=chunk["speed"]
      - use_temp_dir=True  # CRITICAL: Ensures file goes to temp directory
   d. Check tool response for success/error
4. After processing ALL chunks, call cleanup_tts_resources
5. Report: "Synthesized N audio chunks successfully"

## Example Tool Call:
```
synthesize_audio(
  text="The sun rose over the horizon...",
  output_path="chunk_0000.wav",
  reference_audio="reference_audio/male.wav",
  voice="neutral",
  speed=1.0
)
```

## Error Recovery:
If synthesis fails:
- Try rewriting complex text
- Adjust temperature/speed parameters
- Fall back from Replicate to local if needed
- Skip extremely problematic chunks (log warning)

Provide a summary of:
- Total chunks synthesized
- Failed chunks (if any)
- TTS provider used (cloud/local)
- Total audio duration generated
""",
        tools=[read_json_file, synthesize_audio, cleanup_tts_resources]
    )
