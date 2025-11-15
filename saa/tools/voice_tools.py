"""
Voice analysis and character detection tools (ADK function tools)
Multi-strategy character detection for voice assignment
"""
import re
from typing import Dict, Any, List, Tuple
from pathlib import Path

from saa.models import Gender, VoiceProfile
from saa.constants import (
    DIALOGUE_ATTRIBUTION_PATTERNS,
    FEMININE_PRONOUNS,
    MASCULINE_PRONOUNS,
)


def detect_characters(text: str, context: str = "") -> Dict[str, Any]:
    """
    Detect characters in text using multi-strategy analysis.
    
    Employs multiple detection strategies in priority order:
    1. Dialogue attribution patterns ("said Ray", "Julius replied")
    2. Paragraph start analysis (character names at beginning)
    3. First sentence name detection
    4. Pronoun + gender scoring
    5. Fallback to dynamic narrator
    
    Args:
        text: Text segment to analyze
        context: Surrounding context for better detection (optional)
    
    Returns:
        Dictionary with:
            - status: "success"
            - characters: List of detected characters with {name, confidence, method}
            - primary_character: Most likely speaker
            - gender: Detected gender (male/female/neutral/unknown)
            - detection_method: Method used for detection
    """
    try:
        text_lower = text.lower()
        detected = []
        
        # STRATEGY 1: Dialogue attribution patterns (MOST RELIABLE)
        for pattern in DIALOGUE_ATTRIBUTION_PATTERNS:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                name = match.group(1).capitalize()
                detected.append({
                    "name": name,
                    "confidence": 0.9,
                    "method": "dialogue_attribution",
                    "pattern": pattern
                })
        
        # If dialogue attribution found, use it (highest confidence)
        if detected:
            primary = detected[0]
            gender = analyze_text_gender(text)['gender']
            return {
                "status": "success",
                "characters": detected,
                "primary_character": primary['name'],
                "gender": gender,
                "detection_method": "dialogue_attribution",
                "error": None
            }
        
        # STRATEGY 2: Paragraph start analysis
        text_start = text[:100]
        words = text_start.split()
        if words and words[0][0].isupper() and len(words[0]) > 2:
            potential_name = words[0].strip('.,!?;:')
            if _is_likely_name(potential_name):
                gender = analyze_text_gender(text)['gender']
                return {
                    "status": "success",
                    "characters": [{
                        "name": potential_name,
                        "confidence": 0.7,
                        "method": "paragraph_start"
                    }],
                    "primary_character": potential_name,
                    "gender": gender,
                    "detection_method": "paragraph_start",
                    "error": None
                }
        
        # STRATEGY 3: Pronoun + gender analysis (fallback to narrator)
        gender_result = analyze_text_gender(text)
        gender = gender_result['gender']
        
        # Fallback to narrator with detected gender
        narrator_name = f"narrator_{gender}" if gender != "unknown" else "narrator"
        
        return {
            "status": "success",
            "characters": [{
                "name": narrator_name,
                "confidence": 0.5,
                "method": "pronoun_analysis"
            }],
            "primary_character": narrator_name,
            "gender": gender,
            "detection_method": "pronoun_fallback",
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "characters": [],
            "primary_character": "narrator",
            "gender": "unknown",
            "detection_method": "error",
            "error": str(e)
        }


def assign_voice_profile(
    character_name: str,
    gender: str,
    reference_audio_dir: str = "./reference_audio"
) -> Dict[str, Any]:
    """
    Assign voice profile based on character and gender.
    
    Maps detected characters to appropriate voice reference audio files.
    Uses gender-based defaults if character-specific audio unavailable.
    
    Args:
        character_name: Name of character or "narrator"
        gender: Detected gender (male/female/neutral/unknown)
        reference_audio_dir: Directory containing reference audio files
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - voice_profile: Voice profile configuration dict
            - reference_audio: Path to reference audio file
            - character: Character name
            - gender: Gender classification
    """
    try:
        ref_dir = Path(reference_audio_dir)
        
        # Try character-specific audio first
        character_audio = ref_dir / f"{character_name.lower().replace(' ', '_')}.wav"
        
        if character_audio.exists():
            voice_ref = str(character_audio)
        else:
            # Fallback to gender-based default
            if gender.lower() in ['male', 'masculine', 'm']:
                voice_ref = str(ref_dir / "male.wav")
                gender_normalized = "male"
            elif gender.lower() in ['female', 'feminine', 'f']:
                voice_ref = str(ref_dir / "female.wav")
                gender_normalized = "female"
            else:
                # Neutral - try narrator.wav or default to male
                narrator_audio = ref_dir / "narrator.wav"
                if narrator_audio.exists():
                    voice_ref = str(narrator_audio)
                else:
                    voice_ref = str(ref_dir / "male.wav")
                gender_normalized = "neutral"
        
        # Check if file exists
        if not Path(voice_ref).exists():
            return {
                "status": "error",
                "error": f"Reference audio not found: {voice_ref}. "
                        f"Place voice samples in {ref_dir}/"
            }
        
        # Create voice profile
        profile = {
            "name": character_name,
            "gender": gender_normalized,
            "reference_audio": voice_ref,
            "language": "en",
            "temperature": 0.75,
            "speed": 1.0,
            "repetition_penalty": 7.0
        }
        
        return {
            "status": "success",
            "voice_profile": profile,
            "reference_audio": voice_ref,
            "character": character_name,
            "gender": gender_normalized,
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "voice_profile": {},
            "error": str(e)
        }


def analyze_text_gender(text: str) -> Dict[str, Any]:
    """
    Analyze text for gender indicators using pronoun scoring.
    
    Counts masculine vs feminine pronouns to determine likely
    speaker gender. Useful for narrator detection and voice assignment.
    
    Args:
        text: Text to analyze
    
    Returns:
        Dictionary with:
            - gender: "male", "female", "neutral", or "unknown"
            - feminine_score: Count of feminine pronouns
            - masculine_score: Count of masculine pronouns
            - confidence: Confidence level (0.0-1.0)
    """
    try:
        text_lower = text.lower()
        words = set(text_lower.split())
        
        # Count pronouns
        feminine_count = sum(1 for p in FEMININE_PRONOUNS if p in words)
        masculine_count = sum(1 for p in MASCULINE_PRONOUNS if p in words)
        
        total = feminine_count + masculine_count
        
        if total == 0:
            return {
                "gender": "unknown",
                "feminine_score": 0,
                "masculine_score": 0,
                "confidence": 0.0
            }
        
        # Determine gender
        if feminine_count > masculine_count:
            gender = "female"
            confidence = feminine_count / total
        elif masculine_count > feminine_count:
            gender = "male"
            confidence = masculine_count / total
        else:
            gender = "neutral"
            confidence = 0.5
        
        return {
            "gender": gender,
            "feminine_score": feminine_count,
            "masculine_score": masculine_count,
            "confidence": round(confidence, 2)
        }
    
    except Exception as e:
        return {
            "gender": "unknown",
            "feminine_score": 0,
            "masculine_score": 0,
            "confidence": 0.0,
            "error": str(e)
        }


# Helper functions (not exposed as tools)

def _is_likely_name(word: str) -> bool:
    """Check if word is likely a proper name"""
    # Must start with capital
    if not word[0].isupper():
        return False
    
    # Not a common word
    common_words = {
        'The', 'A', 'An', 'As', 'At', 'By', 'For', 'From', 'In', 'Into',
        'Of', 'On', 'To', 'With', 'He', 'She', 'They', 'It', 'This', 'That'
    }
    if word in common_words:
        return False
    
    # Reasonable length (2-15 chars)
    if not (2 <= len(word) <= 15):
        return False
    
    return True
