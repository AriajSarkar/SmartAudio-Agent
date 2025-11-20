"""
Text processing tools (ADK function tools)
Clean, normalize, and segment text for TTS processing
"""
import re
from pathlib import Path
from typing import Dict, Any, List
from saa.models import TextSegment, get_model_provider
from saa.constants import MAX_SEGMENT_LENGTH, SAFE_SEGMENT_LENGTH


def read_text_file(file_path: str) -> Dict[str, Any]:
    """
    Read text content from a file.
    
    Use this tool to load extracted text before processing.
    Typically used to read from output/.temp/extracted/extracted.txt.
    
    Args:
        file_path: Path to text file (e.g., "output/.temp/extracted/extracted.txt")
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - text: File content as string
            - file_path: Path that was read
            - char_count: Number of characters
            - error: Error message if failed
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {
                "status": "error",
                "text": None,
                "file_path": str(file_path),
                "char_count": 0,
                "error": f"File not found: {file_path}"
            }
        
        # Read with UTF-8 encoding
        text = path.read_text(encoding='utf-8')
        
        return {
            "status": "success",
            "text": text,
            "file_path": str(file_path),
            "char_count": len(text),
            "error": None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "text": None,
            "file_path": str(file_path),
            "char_count": 0,
            "error": f"Failed to read file: {str(e)}"
        }


def clean_text(raw_text: str) -> Dict[str, Any]:
    """
    Clean and normalize text for TTS processing.
    
    Removes excessive whitespace, fixes common OCR errors, normalizes
    punctuation, and prepares text for segmentation. Essential for
    high-quality TTS output.
    
    Args:
        raw_text: Raw extracted text from document
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - cleaned_text: Normalized text
            - changes_made: List of cleaning operations performed
            - original_length: Character count before cleaning
            - cleaned_length: Character count after cleaning
    """
    try:
        changes = []
        original_length = len(raw_text)
        
        text = raw_text
        
        # Remove hyphenation at line breaks
        before = text
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        if text != before:
            changes.append("removed_hyphenation")
        
        # Normalize whitespace
        before = text
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        if text != before:
            changes.append("normalized_whitespace")
        
        # Fix common OCR errors
        before = text
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        text = text.replace('–', '-').replace('—', '-')
        if text != before:
            changes.append("fixed_ocr_ligatures")
        
        # Normalize quotes and apostrophes
        before = text
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('`', "'")
        if text != before:
            changes.append("normalized_quotes")
        
        # Remove page numbers and headers/footers
        before = text
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'Page\s+\d+', '', text, flags=re.IGNORECASE)
        if text != before:
            changes.append("removed_page_numbers")
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*([A-Z])', r'\1 \2', text)
        
        # Final trim
        text = text.strip()
        
        cleaned_length = len(text)
        
        return {
            "status": "success",
            "cleaned_text": text,
            "changes_made": changes,
            "original_length": original_length,
            "cleaned_length": cleaned_length,
            "chars_removed": original_length - cleaned_length,
            "summary": f"Cleaned text: {len(changes)} operations, removed {original_length - cleaned_length} chars"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "cleaned_text": "",
            "changes_made": [],
            "error": str(e)
        }


def segment_text(
    text: str,
    max_chars: int = SAFE_SEGMENT_LENGTH,
    preserve_speaker: bool = True
) -> Dict[str, Any]:
    """
    Segment text into TTS-compatible chunks respecting boundaries.
    
    Splits text at sentence boundaries while enforcing the 800-character
    limit required by XTTS-v2. Optionally preserves speaker/dialogue
    boundaries for multi-voice scenarios.
    
    Args:
        text: Cleaned text to segment
        max_chars: Maximum characters per segment (default: 750 for safety margin)
        preserve_speaker: Don't split mid-dialogue (default: True)
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - segments: List of segment dictionaries
            - total_segments: Number of segments created
            - avg_segment_length: Average segment length
            - longest_segment: Length of longest segment
    """
    try:
        if max_chars > MAX_SEGMENT_LENGTH:
            max_chars = SAFE_SEGMENT_LENGTH  # Safety cap
        
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        segments = []
        current_chunk = []
        current_length = 0
        start_pos = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If single sentence exceeds limit, force split at smaller boundary
            if sentence_length > max_chars:
                # Split at comma or semicolon
                sub_parts = re.split(r'(?<=[,;])\s+', sentence)
                for part in sub_parts:
                    if current_length + len(part) > max_chars and current_chunk:
                        # Save current chunk
                        chunk_text = ' '.join(current_chunk)
                        end_pos = start_pos + len(chunk_text)
                        
                        segments.append({
                            "index": len(segments),
                            "text": chunk_text,
                            "start_position": start_pos,
                            "end_position": end_pos,
                            "length": len(chunk_text)
                        })
                        
                        start_pos = end_pos + 1
                        current_chunk = [part]
                        current_length = len(part)
                    else:
                        current_chunk.append(part)
                        current_length += len(part)
            else:
                # Normal sentence handling
                if current_length + sentence_length > max_chars and current_chunk:
                    # Save current chunk
                    chunk_text = ' '.join(current_chunk)
                    end_pos = start_pos + len(chunk_text)
                    
                    segments.append({
                        "index": len(segments),
                        "text": chunk_text,
                        "start_position": start_pos,
                        "end_position": end_pos,
                        "length": len(chunk_text)
                    })
                    
                    start_pos = end_pos + 1
                    current_chunk = [sentence]
                    current_length = sentence_length
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            end_pos = start_pos + len(chunk_text)
            
            segments.append({
                "index": len(segments),
                "text": chunk_text,
                "start_position": start_pos,
                "end_position": end_pos,
                "length": len(chunk_text)
            })
        
        # Calculate statistics
        lengths = [s['length'] for s in segments]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        longest = max(lengths) if lengths else 0
        
        # Save to workspace as chunks.json
        from saa.utils.workspace import WorkspaceManager
        workspace = WorkspaceManager()
        
        # Convert segments to chunks with voice metadata placeholders
        chunks = []
        for seg in segments:
            chunks.append({
                "id": seg["index"],
                "text": seg["text"],
                "voice": "neutral",  # Default, can be updated by voice tools
                "speed": 1.0,
                "emotion": "neutral"
            })
        
        output_file = workspace.save_chunks_json(chunks)
        
        return {
            "status": "success",
            "segments": segments,
            "chunks": chunks,
            "output_file": str(output_file),
            "total_segments": len(segments),
            "avg_segment_length": round(avg_length, 2),
            "longest_segment": longest,
            "summary": f"Created {len(segments)} chunks, avg {round(avg_length)} chars, saved to {output_file.name}",
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "segments": [],
            "chunks": [],
            "output_file": "",
            "total_segments": 0,
            "avg_segment_length": 0,
            "longest_segment": 0,
            "summary": f"Segmentation failed: {str(e)}",
            "error": str(e)
        }


def filter_unwanted_content(text: str, book_title: str = "") -> Dict[str, Any]:
    """
    Remove unwanted content like copyright notices and acknowledgments.
    
    Filters out boilerplate content that shouldn't be in the audiobook:
    copyright blocks, acknowledgments, publication data, etc.
    
    Args:
        text: Full document text
        book_title: Optional book title for smart filtering
    
    Returns:
        Dictionary with:
            - status: "success"
            - filtered_text: Text with unwanted content removed
            - removed_sections: List of section types removed
            - original_length: Length before filtering
            - filtered_length: Length after filtering
    """
    try:
        original_length = len(text)
        filtered = text
        removed = []
        
        # Remove copyright block
        before = filtered
        filtered = re.sub(
            r'Copyright © \d{4}.*?(?=\n\n[A-Z]|\Z)',
            '',
            filtered,
            flags=re.DOTALL | re.MULTILINE
        )
        if filtered != before:
            removed.append("copyright_notice")
        
        # Remove acknowledgments section
        before = filtered
        filtered = re.sub(
            r'A C K N O W L E D G M E N T S.*',
            '',
            filtered,
            flags=re.DOTALL | re.IGNORECASE
        )
        if filtered != before:
            removed.append("acknowledgments")
        
        # Remove page markers and production codes
        before = filtered
        filtered = re.sub(
            r'INT_\d+\.indd.*?\d{1,2}/\d{1,2}/\d{2,4}.*?[AP]M',
            '',
            filtered
        )
        if filtered != before:
            removed.append("page_markers")
        
        # Remove "FOR MY READERS" sections
        before = filtered
        filtered = re.sub(
            r'FOR MY READERS.*?\n',
            '',
            filtered,
            flags=re.IGNORECASE
        )
        if filtered != before:
            removed.append("reader_notes")
        
        # Clean up excessive whitespace created by removals
        filtered = re.sub(r'\n{3,}', '\n\n', filtered)
        filtered = filtered.strip()
        
        return {
            "status": "success",
            "filtered_text": filtered,
            "removed_sections": removed,
            "original_length": original_length,
            "filtered_length": len(filtered),
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "filtered_text": text,
            "removed_sections": [],
            "error": str(e)
        }


def refine_text_for_tts(text: str) -> Dict[str, Any]:
    """
    Refine text to remove TTS-problematic content using LLM.
    
    Uses an agentic approach to intelligently clean text for speech synthesis:
    - Removes decorative elements (dashes like "-------", asterisks, formatting)
    - Normalizes problematic characters and OCR artifacts
    - Fixes awkward sentence structures
    - Preserves meaning while optimizing for natural speech
    
    This function processes text in small context windows to ensure quality
    refinement without changing the core meaning.
    
    Args:
        text: Text chunk to refine (typically 200-250 chars)
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - refined_text: Cleaned text optimized for TTS
            - original_text: Input text for comparison
            - changes_made: List of refinement operations performed
            - char_count_before: Original character count
            - char_count_after: Refined character count
            - error: Error message if failed
    """
    try:
        # Import here to avoid circular dependency
        from google.generativeai import GenerativeModel
        import google.generativeai as genai
        from saa.config import get_settings
        
        settings = get_settings()
        
        # Configure the model
        genai.configure(api_key=settings.google_api_key)
        model = GenerativeModel('gemini-2.0-flash-exp')
        
        # Agentic prompt for text refinement
        prompt = f"""You are a text refinement expert for text-to-speech (TTS) systems.

Your task: Refine the following text to make it TTS-friendly while preserving ALL meaning.

INPUT TEXT:
\"\"\"{text}\"\"\"

REFINEMENT RULES:
1. Remove decorative elements:
   - Dashes used as separators (e.g., "-------", "---")
   - Asterisks used for formatting (e.g., "***", "* * *")
   - Equals signs as dividers (e.g., "=======")

2. Fix TTS-problematic patterns:
   - Convert symbols to words when needed (e.g., "$19.99" → "nineteen ninety-nine dollars")
   - Remove or normalize special formatting characters
   - Fix awkward line breaks mid-sentence

3. PRESERVE completely:
   - All actual content and meaning
   - Proper nouns and names
   - Dialogue and quotes
   - Sentence structure (unless awkward)

4. Output ONLY the refined text, nothing else.
5. If the text is already clean, return it unchanged.
6. Do NOT add explanations or commentary.

REFINED TEXT:"""

        # Call LLM for refinement
        response = model.generate_content(prompt)
        refined_text = response.text.strip()
        
        # Detect changes made
        changes_made = []
        if "---" in text and "---" not in refined_text:
            changes_made.append("removed_decorative_dashes")
        if "***" in text and "***" not in refined_text:
            changes_made.append("removed_asterisks")
        if "===" in text and "===" not in refined_text:
            changes_made.append("removed_equals_dividers")
        if len(refined_text) != len(text):
            changes_made.append("normalized_length")
        if not changes_made:
            changes_made.append("no_changes_needed")
        
        return {
            "status": "success",
            "refined_text": refined_text,
            "original_text": text,
            "changes_made": changes_made,
            "char_count_before": len(text),
            "char_count_after": len(refined_text),
            "summary": f"Refined text: {len(changes_made)} operations, {len(text)} → {len(refined_text)} chars",
            "error": None
        }
    
    except Exception as e:
        # Fallback: return original text if refinement fails
        return {
            "status": "error",
            "refined_text": text,  # Return original on error
            "original_text": text,
            "changes_made": [],
            "char_count_before": len(text),
            "char_count_after": len(text),
            "summary": f"Refinement failed, using original text: {str(e)}",
            "error": str(e)
        }
