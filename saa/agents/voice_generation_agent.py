"""
Voice Generation Agent - Stage 3 of audiobook pipeline (ADK LlmAgent)
Generates audio for each chunk using Gemini-guided TTS synthesis
"""
from google.adk.agents import LlmAgent

from saa.models import get_model_provider
from saa.config import get_settings
from saa.tools.tts_tools import synthesize_audio, cleanup_tts_resources
from saa.tools.file_tools import read_json_file
import json
from pathlib import Path
from typing import Dict, Any

settings = get_settings()


def create_voice_generation_agent() -> LlmAgent:
    """
    Create ADK-based Voice Generation Agent.
    
    Stage 3: Voice Synthesis
    - Reads chunks.json from staging
    - Synthesizes audio for each chunk
    - Handles Replicate/local TTS fallback
    - Saves to .temp/voices/chunk_<id>.wav
    
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
    return LlmAgent(
        name="VoiceGenerationAgent",
        model=get_model_provider(),  # Auto-selects provider from env (Gemini/Ollama/OpenRouter)
        tools=[read_json_file, synthesize_audio, cleanup_tts_resources],
        instruction="""
You are an intelligent voice synthesis agent. You MUST actually synthesize audio files.

## CRITICAL - Your Required Actions:
1. Read chunks.json from: output/.temp/staged/chunks.json
2. For EACH chunk in the JSON array, call synthesize_audio tool
3. Save audio files to output/.temp/voices/chunk_XXXX.wav
4. After all chunks, call cleanup_tts_resources

## Tools Available:
1. **read_json_file** - Read chunks.json file
2. **synthesize_audio** - Generate audio (YOU MUST CALL THIS for each chunk!)
3. **cleanup_tts_resources** - Free GPU memory after synthesis

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
   c. **CALL synthesize_audio tool**:
      - text=chunk["text"]  # Text already refined by TextRefinementAgent!
      - output_path=f"chunk_{chunk['id']:04d}.wav"  # Just filename
      - reference_audio="reference_audio/male.wav" (or appropriate mapping)
      - voice=chunk["voice"]
      - speed=chunk["speed"]
      - use_temp_dir=True  # Saves to output/.temp/voices/
   d. Check tool response for success/error
4. After processing ALL chunks, call cleanup_tts_resources
5. Report: "Synthesized N audio chunks successfully"

## Example Tool Call:
```python
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
"""
    )
