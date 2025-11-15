"""Voice profile and gender models"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Gender(str, Enum):
    """Character gender for voice assignment"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class VoiceProfile:
    """
    Voice configuration for a character or narrator
    
    Attributes:
        name: Profile name (e.g., "narrator", "Julius", "Ray")
        gender: Gender classification
        reference_audio: Path to voice cloning reference audio (6-15s WAV)
        language: Language code (e.g., "en", "es")
        temperature: TTS temperature (0.1-1.0, higher = more expressive)
        speed: Playback speed multiplier (0.5-2.0)
        repetition_penalty: Prevent word repetition (higher = less repetition)
    """
    name: str
    gender: Gender = Gender.NEUTRAL
    reference_audio: Optional[Path] = None
    language: str = "en"
    temperature: float = 0.75
    speed: float = 1.0
    repetition_penalty: float = 7.0
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate profile after initialization"""
        if not 0.1 <= self.temperature <= 1.0:
            raise ValueError(f"Temperature must be 0.1-1.0, got {self.temperature}")
        if not 0.5 <= self.speed <= 2.0:
            raise ValueError(f"Speed must be 0.5-2.0, got {self.speed}")
        if self.reference_audio and not Path(self.reference_audio).exists():
            raise FileNotFoundError(
                f"Reference audio not found: {self.reference_audio}"
            )
    
    @property
    def has_reference_audio(self) -> bool:
        """Check if reference audio is configured"""
        return bool(self.reference_audio and Path(self.reference_audio).exists())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "gender": self.gender.value,
            "reference_audio": str(self.reference_audio) if self.reference_audio else None,
            "language": self.language,
            "temperature": self.temperature,
            "speed": self.speed,
            "repetition_penalty": self.repetition_penalty,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "VoiceProfile":
        """Create from dictionary"""
        data = data.copy()
        if "gender" in data and isinstance(data["gender"], str):
            data["gender"] = Gender(data["gender"])
        if "reference_audio" in data and data["reference_audio"]:
            data["reference_audio"] = Path(data["reference_audio"])
        return cls(**data)
    
    @classmethod
    def create_narrator(
        cls,
        reference_audio: Optional[Path] = None,
        language: str = "en"
    ) -> "VoiceProfile":
        """Factory method for narrator profile"""
        return cls(
            name="narrator",
            gender=Gender.NEUTRAL,
            reference_audio=reference_audio,
            language=language,
        )
    
    @classmethod
    def create_character(
        cls,
        name: str,
        gender: Gender,
        reference_audio: Optional[Path] = None,
        language: str = "en"
    ) -> "VoiceProfile":
        """Factory method for character profile"""
        return cls(
            name=name,
            gender=gender,
            reference_audio=reference_audio,
            language=language,
        )
