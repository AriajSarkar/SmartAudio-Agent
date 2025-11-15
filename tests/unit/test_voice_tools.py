"""Unit tests for voice detection tools"""
import pytest
from saa.tools.voice_tools import (
    detect_characters,
    assign_voice_profile,
    analyze_text_gender,
)


class TestDetectCharacters:
    """Tests for character detection"""
    
    def test_detect_dialogue_attribution(self):
        """Test detection via dialogue attribution"""
        text = '"Hello there," said Gandalf cheerfully.'
        result = detect_characters(text)
        
        assert result["status"] == "success"
        assert result["character"].lower() == "gandalf"
    
    def test_detect_multiple_patterns(self):
        """Test detection with various dialogue patterns"""
        test_cases = [
            ('"Stop!" shouted Sarah.', "sarah"),
            ('John replied, "I agree."', "john"),
            ('"Wait," whispered Emily.', "emily"),
        ]
        
        for text, expected_char in test_cases:
            result = detect_characters(text)
            assert result["character"].lower() == expected_char
    
    def test_detect_narrator_fallback(self):
        """Test narrator detection when no character found"""
        text = "The sun was setting over the mountains."
        result = detect_characters(text)
        
        assert result["status"] == "success"
        assert "narrator" in result["character"].lower()
    
    def test_detect_pronoun_based(self):
        """Test pronoun-based character detection"""
        text = "She walked into the room. Her eyes scanned the area."
        result = detect_characters(text)
        
        assert result["status"] == "success"
        # Should detect female narrator or character


class TestAnalyzeTextGender:
    """Tests for gender analysis"""
    
    def test_analyze_female_pronouns(self):
        """Test detection of female pronouns"""
        text = "She walked to her house. She was happy."
        result = analyze_text_gender(text)
        
        assert result["status"] == "success"
        assert result["gender"] == "female"
        assert result["confidence"] > 0.5
    
    def test_analyze_male_pronouns(self):
        """Test detection of male pronouns"""
        text = "He went to his car. He drove away."
        result = analyze_text_gender(text)
        
        assert result["status"] == "success"
        assert result["gender"] == "male"
        assert result["confidence"] > 0.5
    
    def test_analyze_neutral_text(self):
        """Test neutral text analysis"""
        text = "The weather was nice. It was sunny."
        result = analyze_text_gender(text)
        
        assert result["status"] == "success"
        assert result["gender"] in ["neutral", "unknown"]
    
    def test_analyze_mixed_pronouns(self):
        """Test text with mixed pronouns"""
        text = "He and she went together."
        result = analyze_text_gender(text)
        
        assert result["status"] == "success"
        # Should return most dominant or neutral


class TestAssignVoiceProfile:
    """Tests for voice profile assignment"""
    
    def test_assign_male_voice(self):
        """Test assignment of male voice"""
        result = assign_voice_profile(
            character="John",
            gender="male",
            reference_audio_dir="reference_audio"
        )
        
        assert result["status"] == "success"
        assert "male.wav" in result["voice_profile"]["reference_audio"]
    
    def test_assign_female_voice(self):
        """Test assignment of female voice"""
        result = assign_voice_profile(
            character="Sarah",
            gender="female",
            reference_audio_dir="reference_audio"
        )
        
        assert result["status"] == "success"
        assert "female.wav" in result["voice_profile"]["reference_audio"]
    
    def test_assign_narrator_voice(self):
        """Test assignment of narrator voice"""
        result = assign_voice_profile(
            character="Narrator",
            gender="neutral",
            reference_audio_dir="reference_audio"
        )
        
        assert result["status"] == "success"
        assert "narrator.wav" in result["voice_profile"]["reference_audio"]
    
    def test_voice_profile_structure(self):
        """Test voice profile has required fields"""
        result = assign_voice_profile("Test", "male")
        
        assert result["status"] == "success"
        profile = result["voice_profile"]
        assert "name" in profile
        assert "gender" in profile
        assert "reference_audio" in profile
        assert "temperature" in profile
        assert "speed" in profile
