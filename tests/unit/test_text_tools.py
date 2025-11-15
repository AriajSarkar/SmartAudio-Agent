"""Unit tests for text processing tools"""
import pytest
from saa.tools.text_tools import (
    clean_text,
    segment_text,
    filter_unwanted_content,
)


class TestCleanText:
    """Tests for text cleaning"""
    
    def test_clean_basic_text(self):
        """Test cleaning of basic text"""
        text = "This is a  simple   text."
        result = clean_text(text)
        
        assert result["status"] == "success"
        assert "simple text" in result["cleaned_text"]
    
    def test_clean_hyphenation(self):
        """Test removal of hyphenation"""
        text = "This is a hyphen-\nated word."
        result = clean_text(text)
        
        assert result["status"] == "success"
        assert "hyphenated" in result["cleaned_text"]
    
    def test_clean_multiple_spaces(self):
        """Test normalization of multiple spaces"""
        text = "Too    many     spaces"
        result = clean_text(text)
        
        assert result["status"] == "success"
        assert "  " not in result["cleaned_text"]
    
    def test_clean_empty_text(self):
        """Test cleaning empty text"""
        result = clean_text("")
        
        assert result["status"] == "success"
        assert result["cleaned_text"] == ""


class TestSegmentText:
    """Tests for text segmentation"""
    
    def test_segment_short_text(self):
        """Test segmentation of short text"""
        text = "This is a short sentence."
        result = segment_text(text, max_length=100)
        
        assert result["status"] == "success"
        assert len(result["segments"]) == 1
        assert result["segments"][0]["text"] == text
    
    def test_segment_respects_max_length(self):
        """Test that segments respect max length"""
        text = "A " * 500  # 1000 chars
        result = segment_text(text, max_length=800)
        
        assert result["status"] == "success"
        for segment in result["segments"]:
            assert len(segment["text"]) <= 800
    
    def test_segment_respects_sentence_boundaries(self):
        """Test that segments break at sentence boundaries"""
        text = "First sentence. " * 100
        result = segment_text(text, max_length=500)
        
        assert result["status"] == "success"
        # Each segment should end with period
        for segment in result["segments"]:
            assert segment["text"].rstrip().endswith(".")
    
    def test_segment_empty_text(self):
        """Test segmentation of empty text"""
        result = segment_text("")
        
        assert result["status"] == "success"
        assert len(result["segments"]) == 0


class TestFilterUnwantedContent:
    """Tests for content filtering"""
    
    def test_filter_copyright(self):
        """Test removal of copyright notices"""
        text = "Copyright © 2024 Author. All rights reserved.\n\nActual content here."
        result = filter_unwanted_content(text)
        
        assert result["status"] == "success"
        assert "Copyright" not in result["filtered_text"]
        assert "Actual content" in result["filtered_text"]
    
    def test_filter_acknowledgments(self):
        """Test removal of acknowledgments"""
        text = "A C K N O W L E D G M E N T S\n\nThanks to everyone.\n\nChapter 1"
        result = filter_unwanted_content(text)
        
        assert result["status"] == "success"
        assert "ACKNOWLEDGMENTS" not in result["filtered_text"]
        assert "Chapter 1" in result["filtered_text"]
    
    def test_filter_page_numbers(self):
        """Test removal of page numbers"""
        text = "Content here\nINT_123.indd 45 10/15/2024 3:45 PM\nMore content"
        result = filter_unwanted_content(text)
        
        assert result["status"] == "success"
        assert "INT_" not in result["filtered_text"]
        assert "Content here" in result["filtered_text"]
    
    def test_filter_preserves_content(self):
        """Test that filtering preserves main content"""
        text = "This is the main story content."
        result = filter_unwanted_content(text)
        
        assert result["status"] == "success"
        assert result["filtered_text"] == text
