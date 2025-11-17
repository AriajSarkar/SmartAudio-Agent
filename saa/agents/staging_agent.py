"""
Staging Agent - Stage 2 of audiobook pipeline (ADK LlmAgent)
Cleans text, creates chunks, applies voice metadata using Gemini intelligence
"""
from google.adk.agents import LlmAgent
from google.adk.models import Gemini

from saa.config import get_settings
from saa.tools.text_tools import read_text_file, clean_text, segment_text, filter_unwanted_content
from saa.tools.voice_tools import detect_characters, analyze_text_gender, assign_voice_profile

settings = get_settings()


def create_staging_agent() -> LlmAgent:
    """
    Create ADK-based Staging Agent.
    
    Stage 2: Chunking + Cleaning + Voice Metadata
    - Cleans and segments text intelligently
    - Detects characters and voice requirements
    - Creates chunks.json with voice metadata
    - Saves to .temp/staged/chunks.json
    
    Gemini Intelligence:
    - Recognizes garbage text vs meaningful content
    - Understands natural speech breaks
    - Detects gender/emotion from context
    - Assigns appropriate voice profiles
    - Plans pacing and prosody adjustments
    
    JSON Output Format:
    {
      "chunks": [
        {
          "id": 0,
          "text": "cleaned chunk text",
          "voice": "male",
          "speed": 1.0,
          "emotion": "neutral"
        }
      ]
    }
    
    Returns:
        LlmAgent configured for text staging
    """
    return LlmAgent(
        name="StagingAgent",
        model=Gemini(model=settings.gemini_text_model),
        instruction="""
You are an intelligent text staging agent.

Your task is to clean, segment, and plan voice metadata for audiobook chunks.

## Input:
You will be given the extracted text path from the coordinator. Read from: **output/.temp/extracted/extracted.txt**

## Tools Available:
1. **read_text_file** - Read text from extracted file
2. **clean_text** - Remove formatting artifacts, fix spacing
3. **filter_unwanted_content** - Remove copyright, headers, metadata
4. **segment_text** - Split into speech-friendly chunks
5. **detect_characters** - Find dialogue and character names
6. **analyze_text_gender** - Detect masculine/feminine tone
7. **assign_voice_profile** - Assign voice characteristics

## Your Intelligence:
Think about the text structure:
- Is this garbage text or meaningful content?
- Where are natural speech breaks (sentences, paragraphs)?
- Is this dialogue or narration?
- What gender voice fits this section?
- Should pacing be fast (action) or slow (description)?
- What emotional tone (neutral, excited, somber)?

## Workflow:
1. **Read the extracted text file** using read_text_file("output/.temp/extracted/extracted.txt")
2. **VERIFY read_text_file response**:
   - Check status == "success"
   - Confirm text field contains content
   - Review char_count
3. Clean the text using clean_text (remove artifacts)
3. Clean the text using clean_text (remove artifacts)
4. **VERIFY clean_text response**:
   - Check status == "success"
   - Review changes_made array
   - Confirm chars_removed count
5. Filter unwanted content (if needed)
6. Segment into chunks (~750 chars each)
7. **VERIFY segment_text response**:
   - Check status == "success"
   - Confirm output_file created (chunks.json)
   - Review total_segments count
   - Verify chunks array has {id, text, voice, speed, emotion}
8. Communicate: "OK - Created [N] chunks, saved to [path]"

## Expected Tool Response from segment_text:
{
  "status": "success",
  "chunks": [{"id": 0, "text": "...", "voice": "neutral", "speed": 1.0, "emotion": "neutral"}],
  "output_file": "output/.temp/staged/chunks.json",
  "total_segments": N,
  "summary": "Created N chunks..."
}

**CRITICAL**: After each tool call, verify response format!
If unexpected format, explain what you expected vs what you got.
""",
        tools=[read_text_file, clean_text, filter_unwanted_content, segment_text, 
               detect_characters, analyze_text_gender, assign_voice_profile]
    )
