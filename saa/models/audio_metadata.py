"""Audio metadata and chunk models"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime


@dataclass
class AudioMetadata:
    """
    Metadata for audio files
    
    Attributes:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        channels: Number of audio channels
        format: Audio format (mp3, wav, etc.)
        bitrate: Bitrate in kbps (for compressed formats)
        file_size: File size in bytes
    """
    duration: float
    sample_rate: int = 24000
    channels: int = 1
    format: str = "wav"
    bitrate: Optional[int] = None
    file_size: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "format": self.format,
            "bitrate": self.bitrate,
            "file_size": self.file_size,
        }


@dataclass
class AudioChunk:
    """
    Represents a generated audio chunk
    
    Attributes:
        index: Chunk index in sequence
        file_path: Path to audio file
        segment_index: Index of corresponding text segment
        character: Character name (if multi-voice)
        metadata: Audio metadata
        synthesis_method: Method used (replicate, local)
        generated_at: Timestamp
    """
    index: int
    file_path: Path
    segment_index: int
    character: Optional[str] = None
    metadata: Optional[AudioMetadata] = None
    synthesis_method: str = "local"
    generated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Validate chunk after initialization"""
        if not Path(self.file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {self.file_path}")
    
    @property
    def exists(self) -> bool:
        """Check if audio file exists"""
        return Path(self.file_path).exists()
    
    @property
    def size_bytes(self) -> int:
        """Get file size in bytes"""
        return Path(self.file_path).stat().st_size if self.exists else 0
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB"""
        return self.size_bytes / (1024 * 1024)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "index": self.index,
            "file_path": str(self.file_path),
            "segment_index": self.segment_index,
            "character": self.character,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "synthesis_method": self.synthesis_method,
            "generated_at": self.generated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AudioChunk":
        """Create from dictionary"""
        data = data.copy()
        if "file_path" in data:
            data["file_path"] = Path(data["file_path"])
        if "metadata" in data and data["metadata"]:
            data["metadata"] = AudioMetadata(**data["metadata"])
        if "generated_at" in data and isinstance(data["generated_at"], str):
            data["generated_at"] = datetime.fromisoformat(data["generated_at"])
        return cls(**data)
