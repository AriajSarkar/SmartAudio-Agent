"""
Extraction Agent - Stage 1 of audiobook pipeline (ADK LlmAgent)
Extracts raw text from PDF or TXT files using Gemini intelligence
"""
from google.adk.agents import LlmAgent
from google.adk.models import Gemini

from saa.config import get_settings
from saa.tools.document_tools import extract_text_from_pdf, extract_text_from_txt, get_document_metadata

settings = get_settings()


def create_extraction_agent() -> LlmAgent:
    """
    Create ADK-based Extraction Agent.
    
    Stage 1: Document Extraction
    - Extracts raw text from PDF/TXT
    - Understands document structure (chapters, metadata)
    - Saves to .temp/extracted/extracted.txt
    
    Gemini Intelligence:
    - Identifies document type and structure
    - Detects chapter breaks vs continuous text
    - Filters metadata (TOC, headers, footers)
    - Recognizes dialogue vs narration sections
    
    Returns:
        LlmAgent configured for document extraction
    """
    return LlmAgent(
        name="ExtractionAgent",
        model=Gemini(model=settings.gemini_text_model),
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
