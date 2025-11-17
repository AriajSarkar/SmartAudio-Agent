"""
Extraction Agent - Stage 1 of audiobook pipeline (ADK LlmAgent)
Extracts raw text from PDF or TXT files using Gemini intelligence
"""
from google.adk.agents import LlmAgent

from saa.config import get_settings
from saa.models import get_model_provider
from saa.tools.document_tools import extract_text_from_pdf, extract_text_from_txt, get_document_metadata

settings = get_settings()


def create_extraction_agent() -> LlmAgent:
    """
    Create ADK-based Extraction Agent.
    
    Stage 1: Document Extraction
    - Extracts raw text from PDF/TXT
    - Understands document structure (chapters, metadata)
    - Saves to .temp/extracted/extracted.txt
    
    GEMINI INTELLIGENCE - What AI Decides:
    ======================================
    
    1. Document Type Recognition:
       - Is this a PDF or TXT file? (file extension analysis)
       - Which extraction tool should I call? (pdf vs txt)
    
    2. Structure Understanding:
       - Are there chapter headings? ("Chapter 1", "Part I")
       - Is this a novel, textbook, or article? (formatting patterns)
       - Should I preserve or merge paragraphs? (spacing analysis)
    
    3. Metadata Filtering:
       - Are these page numbers to ignore? ("Page 23")
       - Is this a table of contents? ("Chapter ... Page")
       - Are these headers/footers? (repeated at top/bottom)
    
    4. Content Classification:
       - Is this dialogue or narration? (quotation marks)
       - Are there multiple speakers? (character names)
       - Is this descriptive or action text? (verb tense, pacing)
    
    5. Quality Verification:
       - Does the extracted text make sense? (coherence check)
       - Are there OCR errors to flag? (garbled characters)
       - Is character count reasonable? (not empty or truncated)
    
    WHY AI? (Why This Needs Intelligence):
    --------------------------------------
    WHY THIS MATTERS:
    ----------------
    Without Gemini intelligence, you'd get:
    - Raw extracted text with page numbers mixed in
    - Headers/footers repeated every page
    - No understanding of structure for later stages
    
    With Gemini, you get:
    - Clean text ready for segmentation
    - Structural hints for voice assignment
    - Quality-checked output
    
    Returns:
        LlmAgent configured for intelligent document extraction
    """
    return LlmAgent(
        name="ExtractionAgent",
        model=get_model_provider(),  # Auto-selects provider from env (Gemini/Ollama/OpenRouter)
        instruction="""
You are an intelligent document extraction agent.

Your task is to extract and understand document structure from PDF or TXT files.

## Tools Available:
1. **extract_text_from_pdf** - Extract text from PDF documents
2. **extract_text_from_txt** - Extract text from TXT files
3. **get_document_metadata** - Get document metadata

## Your Intelligence:
Think about the document structure:
- Is this a book with chapters or a single passage?
- Are there headers, footers, or page numbers to ignore?
- Is there a Table of Contents to recognize?
- Are there dialogue sections vs narration?
- Should paragraphs be merged or kept separate?

## Workflow:
1. Identify file type (PDF or TXT)
2. Extract raw text using appropriate tool
3. **VERIFY tool response**:
   - Check status == "success"
   - Confirm output_file was created
   - Review total_chars and total_pages
   - Read summary field
4. If extraction fails (status="error"), report the error details
5. If successful, communicate: "OK - Extracted [X] pages, [Y] characters. File saved to [path]"

## Expected Tool Response:
{
  "status": "success",
  "text": "extracted content...",
  "output_file": "output/.temp/extracted/extracted.txt",
  "total_pages": N,
  "total_chars": M,
  "summary": "Extracted N pages, M characters from PDF"
}

**CRITICAL**: After tool call, verify the response matches expected format!
If you get unexpected format, explain what you expected vs what you got.
""",
        tools=[extract_text_from_pdf, extract_text_from_txt, get_document_metadata]
    )
