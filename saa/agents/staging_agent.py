"""
Staging Agent - Stage 2 of audiobook pipeline (ADK LlmAgent)
Cleans text, creates chunks, applies voice metadata using Gemini intelligence
"""
from google.adk.agents import LlmAgent

from saa.models import get_model_provider
from saa.tools.text_tools import read_text_file, clean_text, segment_text, filter_unwanted_content
from saa.tools.voice_tools import detect_characters, analyze_text_gender, assign_voice_profile


def create_staging_agent() -> LlmAgent:
    """
    Create ADK-based Staging Agent.
    
    Stage 2: Chunking + Cleaning + Voice Metadata
    - Cleans and segments text intelligently
    - Detects characters and voice requirements
    - Creates chunks.json with voice metadata
    - Saves to .temp/staged/chunks.json
    
    GEMINI INTELLIGENCE - Critical Decision Points:
    ==============================================
    
    1. Garbage Text Recognition:
       DECISION: "Is this meaningful content or OCR artifacts?"
       - "The sun rose over..." → Keep (coherent)
       - "xJ3!@ f00t3r txt" → Remove (garbage)
       - "Page 42" repeated → Remove (metadata)
       
       WHY AI?: Regex can't distinguish context-dependent garbage
    
    2. Natural Speech Breaks:
       DECISION: "Where should I split for natural speech?"
       - Mid-sentence split: "The cat sat on the..." → BAD
       - Sentence boundary: "...on the mat. The dog barked." → GOOD
       - Paragraph boundary: "...barked loudly.\n\nMeanwhile..." → BETTER
       
       WHY AI?: Understanding semantic boundaries, not just character count
    
    3. Gender/Emotion Detection:
       DECISION: "What voice characteristics fit this text?"
       - "He shouted angrily, 'Stop!'" → male, fast, angry
       - "She whispered softly..." → female, slow, gentle
       - "The narrator explained..." → neutral, medium, calm
       
       WHY AI?: Context-aware emotion, not keyword matching
    
    4. Voice Profile Assignment:
       DECISION: "Which voice profile best matches this chunk?"
       - Dialogue from John → male voice, character consistency
       - Dialogue from Mary → female voice, different character
       - Narration → neutral/narrator voice
       
       WHY AI?: Tracks character identity across chunks
    
    5. Pacing Adjustments:
       DECISION: "How fast should this be read?"
       - Action scene: "The car sped..." → speed=1.2 (faster)
       - Description: "The peaceful garden..." → speed=0.9 (slower)
       - Dialogue: Normal speed → speed=1.0
       
       WHY AI?: Understands narrative pacing from content
    
    ARCHITECTURE NOTE: Why This Stage Exists
    ========================================
    We could do "dumb chunking" (split every N chars), but that results in:
    - ❌ Mid-sentence breaks ("The cat sat on the... [break] ...mat")
    - ❌ Wrong voices (male narrator voice for female character)
    - ❌ Monotone audio (all same speed/emotion)
    
    With Gemini intelligence:
    - ✅ Natural speech breaks (sentence/paragraph boundaries)
    - ✅ Context-aware voice assignment (character tracking)
    - ✅ Dynamic pacing (action vs description)
    
    JSON Output Format:
    {
      "chunks": [
        {
          "id": 0,
          "text": "cleaned chunk text",
          "voice": "male",         # AI-assigned voice
          "speed": 1.0,            # AI-determined pacing
          "emotion": "neutral"     # AI-detected emotion
        }
      ]
    }
    
    Returns:
        LlmAgent configured for intelligent text staging
    """
    return LlmAgent(
        name="StagingAgent",
        model=get_model_provider(),  # Auto-selects provider from env (Gemini/Ollama/OpenRouter)
        tools=[read_text_file, clean_text, segment_text, filter_unwanted_content,
               detect_characters, analyze_text_gender, assign_voice_profile],
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
"""
    )
