"""Text segment data model"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class TextSegment:
    """
    Represents a segment of text for TTS processing
    
    Attributes:
        index: Sequential index in the document
        text: The text content (max 800 chars for XTTS-v2)
        character: Optional character name (for multi-voice)
        speaker: Speaker identifier (for voice assignment)
        start_position: Character position in original document
        end_position: Character position in original document
        metadata: Additional segment metadata
    """
    index: int
    text: str
    character: Optional[str] = None
    speaker: Optional[str] = "narrator"
    start_position: int = 0
    end_position: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate segment after initialization"""
        if len(self.text) > 800:
            raise ValueError(
                f"Segment text too long: {len(self.text)} chars (max 800)"
            )
        if len(self.text) < 10:
            raise ValueError(
                f"Segment text too short: {len(self.text)} chars (min 10)"
            )
    
    @property
    def length(self) -> int:
        """Get text length"""
        return len(self.text)
    
    @property
    def word_count(self) -> int:
        """Estimate word count"""
        return len(self.text.split())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "index": self.index,
            "text": self.text,
            "character": self.character,
            "speaker": self.speaker,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TextSegment":
        """Create from dictionary"""
        data = data.copy()
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
