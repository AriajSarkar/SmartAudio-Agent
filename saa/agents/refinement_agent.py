"""
Text Refinement Agent - Stage 2.5 of audiobook pipeline (ADK LlmAgent)
Refines text chunks to remove TTS-problematic content before synthesis
"""
from google.adk.agents import LlmAgent

from saa.models import get_model_provider
from saa.tools.text_tools import refine_text_for_tts, read_text_file
from saa.tools.file_tools import read_json_file, update_chunk_text


def create_refinement_agent() -> LlmAgent:
    """
    Create Text Refinement Agent.
    
    Stage 2.5: Text Refinement (NEW!)
    - Reads chunks.json from staging
    - Refines each chunk's text using LLM
    - Removes dashes, formatting artifacts, OCR errors
    - Saves refined chunks back to chunks.json
    
    This stage runs BETWEEN staging and voice generation to ensure
    the chunks.json itself contains clean, TTS-ready text.
    
    Returns:
        LlmAgent configured for text refinement
    """
    return LlmAgent(
        name="TextRefinementAgent",
        model=get_model_provider(),
        tools=[read_json_file, refine_text_for_tts, update_chunk_text, read_text_file],
        instruction="""
You are a text refinement agent. Your job is to clean text chunks before TTS synthesis.

## CRITICAL - Context Awareness:
1. FIRST, read `output/.temp/extracted/extracted.txt` using `read_text_file`.
2. Analyze the document type (e.g., "Technical Demo", "Novel", "Medical Paper").
3. Use this context to identify "garbage".
   - In a "Technical Demo", "cutieee pieeee" is GARBAGE.
   - In a "Romance Novel", "cutieee pieeee" might be DIALOGUE.

## Your Required Actions:
1. Read extracted text for context.
2. Read chunks.json from: output/.temp/staged/chunks.json
3. For EACH chunk:
   a. Refine the text using refine_text_for_tts
   b. IF the text changed or needs cleaning:
      - Call update_chunk_text(file_path, chunk_id, new_text)
      - This saves the change immediately!

## Tools Available:
1. **read_text_file** - Read extracted.txt for CONTEXT
2. **read_json_file** - Read chunks.json
3. **refine_text_for_tts** - Clean text (removes dashes, formatting, OCR errors)
4. **update_chunk_text** - Update a SPECIFIC chunk's text (Granular Update)

## Step-by-Step Workflow:
1. Read `output/.temp/extracted/extracted.txt` to understand the document.
2. Read chunks.json from output/.temp/staged/chunks.json
3. Parse the "chunks" array
3. For each chunk in the array:
   a. Check text for:
      - Garbage ("cutieee pieeee", "rhgdo") -> REMOVE or FIX
      - Formatting ("-------", "***") -> REMOVE
      - Page numbers -> REMOVE
   b. Call refine_text_for_tts(chunk["text"])
   c. Compare refined text with original.
   d. IF different:
      - Call update_chunk_text(
          file_path="output/.temp/staged/chunks.json",
          chunk_id=chunk["id"],
          new_text=refined_text
        )
4. Report: "Refined N chunks successfully"

## Example:
Chunk 3: "-------rhgdo\\nUnlike traditional..."
Refined: "Unlike traditional..."
Action: update_chunk_text(..., chunk_id=3, new_text="Unlike traditional...")

**CRITICAL**: You must be aggressive with garbage removal. If a chunk is PURE GARBAGE (e.g. "gseiojg"), replace it with a generic placeholder like "..." or remove the content entirely if possible.
"""
    )
