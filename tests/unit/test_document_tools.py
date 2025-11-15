"""Unit tests for document processing tools"""
import pytest
from pathlib import Path
from saa.tools.document_tools import (
    extract_text_from_pdf,
    extract_text_from_txt,
    get_document_metadata,
)


class TestExtractTextFromPDF:
    """Tests for PDF text extraction"""
    
    def test_extract_pdf_success(self, sample_pdf_path):
        """Test successful PDF extraction"""
        result = extract_text_from_pdf(str(sample_pdf_path))
        
        assert result["status"] == "success"
        assert "text" in result
        assert len(result["text"]) > 0
        assert result["error"] is None
    
    def test_extract_pdf_file_not_found(self):
        """Test PDF extraction with non-existent file"""
        result = extract_text_from_pdf("/path/to/nonexistent.pdf")
        
        assert result["status"] == "error"
        assert result["text"] == ""
        assert result["error"] is not None
    
    def test_extract_pdf_invalid_file(self, temp_dir):
        """Test PDF extraction with invalid file"""
        invalid_pdf = temp_dir / "invalid.pdf"
        invalid_pdf.write_text("This is not a PDF")
        
        result = extract_text_from_pdf(str(invalid_pdf))
        
        # Should still return something (might use fallback)
        assert result["status"] in ["success", "error"]


class TestExtractTextFromTXT:
    """Tests for TXT text extraction"""
    
    def test_extract_txt_utf8(self, sample_txt_path):
        """Test UTF-8 TXT extraction"""
        result = extract_text_from_txt(str(sample_txt_path))
        
        assert result["status"] == "success"
        assert "Gandalf" in result["text"]
        assert result["error"] is None
    
    def test_extract_txt_different_encodings(self, temp_dir):
        """Test TXT extraction with different encodings"""
        # Latin-1 encoded file
        latin1_path = temp_dir / "latin1.txt"
        latin1_path.write_bytes("Café résumé".encode("latin-1"))
        
        result = extract_text_from_txt(str(latin1_path))
        
        assert result["status"] == "success"
        assert len(result["text"]) > 0
    
    def test_extract_txt_file_not_found(self):
        """Test TXT extraction with non-existent file"""
        result = extract_text_from_txt("/path/to/nonexistent.txt")
        
        assert result["status"] == "error"
        assert result["text"] == ""
        assert "not found" in result["error"].lower()


class TestGetDocumentMetadata:
    """Tests for document metadata extraction"""
    
    def test_metadata_success(self, sample_text):
        """Test successful metadata extraction"""
        result = get_document_metadata(sample_text)
        
        assert result["status"] == "success"
        assert result["word_count"] > 0
        assert result["estimated_pages"] > 0
        assert result["estimated_duration_minutes"] > 0
        assert result["error"] is None
    
    def test_metadata_empty_text(self):
        """Test metadata with empty text"""
        result = get_document_metadata("")
        
        assert result["status"] == "success"
        assert result["word_count"] == 0
        assert result["estimated_pages"] == 0
        assert result["estimated_duration_minutes"] == 0
    
    def test_metadata_short_text(self):
        """Test metadata with short text"""
        result = get_document_metadata("Hello world")
        
        assert result["status"] == "success"
        assert result["word_count"] == 2
        assert result["estimated_pages"] == 1  # Minimum 1 page
        assert result["estimated_duration_minutes"] > 0
