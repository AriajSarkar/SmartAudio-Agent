"""
Document processing tools (ADK function tools)
These functions are auto-discovered by ADK agents via docstrings and type hints
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import PyPDF2
import pdfplumber

from saa.exceptions import (
    FileNotFoundError as SAAFileNotFoundError,
    UnsupportedFormatError,
    DocumentError,
)
from saa.constants import SUPPORTED_INPUT_FORMATS


def extract_text_from_pdf(file_path: str, use_pdfplumber: bool = True) -> Dict[str, Any]:
    """
    Extract text from PDF file using pdfplumber or PyPDF2.
    
    This function reads a PDF document and extracts all text content,
    cleaning and normalizing it for TTS processing. Returns both the
    full text and page-by-page breakdown.
    
    Args:
        file_path: Absolute path to PDF file
        use_pdfplumber: Use pdfplumber (better quality) vs PyPDF2 (faster)
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - text: Full extracted text
            - pages: List of page objects with {number, text}
            - metadata: PDF metadata dict
            - error: Error message if failed
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            raise SAAFileNotFoundError(str(path))
        
        if path.suffix.lower() != '.pdf':
            raise UnsupportedFormatError(path.suffix, ('.pdf',))
        
        pages = []
        metadata = {}
        
        if use_pdfplumber:
            with pdfplumber.open(path) as pdf:
                metadata = pdf.metadata or {}
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        cleaned = _clean_page_text(text)
                        pages.append({
                            'number': page_num,
                            'text': cleaned
                        })
        else:
            with open(path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = dict(pdf_reader.metadata or {})
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        cleaned = _clean_page_text(text)
                        pages.append({
                            'number': page_num,
                            'text': cleaned
                        })
        
        # Combine all pages
        full_text = "\n\n".join(p['text'] for p in pages)
        
        return {
            "status": "success",
            "text": full_text,
            "pages": pages,
            "metadata": metadata,
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "text": "",
            "pages": [],
            "metadata": {},
            "error": str(e)
        }


def extract_text_from_txt(file_path: str) -> Dict[str, Any]:
    """
    Extract text from TXT file with encoding fallback.
    
    Attempts multiple encodings (UTF-8, Latin-1, CP1252) to read
    text files. Splits content into pseudo-pages for consistency
    with PDF processing.
    
    Args:
        file_path: Absolute path to TXT file
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - text: Full extracted text
            - pages: List of page objects (500 words per "page")
            - error: Error message if failed
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            raise SAAFileNotFoundError(str(path))
        
        if path.suffix.lower() != '.txt':
            raise UnsupportedFormatError(path.suffix, ('.txt',))
        
        # Try multiple encodings
        text = None
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if text is None:
            raise DocumentError(f"Could not decode file with any encoding")
        
        # Clean text
        cleaned = _clean_text_content(text)
        
        # Split into pseudo-pages (500 words each)
        words = cleaned.split()
        page_size = 500
        pages = []
        
        for i in range(0, len(words), page_size):
            page_text = ' '.join(words[i:i + page_size])
            pages.append({
                'number': (i // page_size) + 1,
                'text': page_text
            })
        
        return {
            "status": "success",
            "text": cleaned,
            "pages": pages,
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "text": "",
            "pages": [],
            "error": str(e)
        }


def get_document_metadata(file_path: str) -> Dict[str, Any]:
    """
    Get metadata and statistics for a document file.
    
    Extracts file information, estimates reading time, and provides
    statistics useful for planning TTS generation.
    
    Args:
        file_path: Path to PDF or TXT file
    
    Returns:
        Dictionary with:
            - filename: File name
            - file_type: "PDF" or "Text File"
            - pages: Number of pages
            - total_characters: Character count
            - total_words: Word count
            - estimated_duration_minutes: Estimated audio duration
            - file_size_mb: File size in megabytes
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            raise SAAFileNotFoundError(str(path))
        
        file_type = path.suffix.lower()
        
        if file_type == '.pdf':
            result = extract_text_from_pdf(file_path)
        elif file_type == '.txt':
            result = extract_text_from_txt(file_path)
        else:
            raise UnsupportedFormatError(file_type, SUPPORTED_INPUT_FORMATS)
        
        if result['status'] != 'success':
            return {
                "status": "error",
                "error": result['error']
            }
        
        text = result['text']
        pages = result['pages']
        
        word_count = len(text.split())
        char_count = len(text)
        
        # Estimate duration (150 words per minute average reading speed)
        estimated_minutes = word_count / 150
        
        return {
            "status": "success",
            "filename": path.name,
            "file_type": "PDF" if file_type == '.pdf' else "Text File",
            "pages": len(pages),
            "total_characters": char_count,
            "total_words": word_count,
            "estimated_duration_minutes": round(estimated_minutes, 2),
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Helper functions (not exposed as tools)

def _clean_page_text(text: str) -> str:
    """Clean and normalize extracted PDF page text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'Page\s+\d+', '', text, flags=re.IGNORECASE)
    
    # Fix common OCR issues
    text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    text = text.replace('–', '-').replace('—', '-')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('"', '"').replace('"', '"')
    
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    
    return text.strip()


def _clean_text_content(text: str) -> str:
    """Clean text from TXT files"""
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove excessive whitespace while preserving paragraphs
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()
