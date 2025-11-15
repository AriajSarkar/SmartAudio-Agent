"""Job state and processing stage models"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path


class ProcessingStage(str, Enum):
    """Pipeline processing stages"""
    PENDING = "pending"
    DOCUMENT_LOAD = "document_load"
    TEXT_CLEANING = "text_cleaning"
    SEGMENTATION = "segmentation"
    VOICE_PLANNING = "voice_planning"
    SYNTHESIS = "synthesis"
    AUDIO_MERGE = "audio_merge"
    FINALIZATION = "finalization"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobState:
    """
    Complete job state for checkpoint/resume
    
    Attributes:
        job_id: Unique job identifier
        input_file: Path to input document
        output_dir: Job output directory
        stage: Current processing stage
        total_segments: Total number of segments
        completed_segments: List of completed segment indices
        failed_segments: List of failed segment indices
        audio_chunks: List of generated audio chunk paths
        config_snapshot: Configuration at job creation
        started_at: Job start timestamp
        updated_at: Last update timestamp
        completed_at: Completion timestamp
        error: Error message if failed
    """
    job_id: str
    input_file: Path
    output_dir: Path
    stage: ProcessingStage = ProcessingStage.PENDING
    total_segments: int = 0
    completed_segments: List[int] = field(default_factory=list)
    failed_segments: List[int] = field(default_factory=list)
    audio_chunks: List[str] = field(default_factory=list)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_completed(self) -> bool:
        """Check if job completed successfully"""
        return self.stage == ProcessingStage.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if job failed"""
        return self.stage == ProcessingStage.FAILED
    
    @property
    def is_processing(self) -> bool:
        """Check if job is actively processing"""
        return self.stage not in [
            ProcessingStage.PENDING,
            ProcessingStage.COMPLETED,
            ProcessingStage.FAILED,
            ProcessingStage.CANCELLED,
        ]
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_segments == 0:
            return 0.0
        return (len(self.completed_segments) / self.total_segments) * 100
    
    @property
    def pending_segments(self) -> List[int]:
        """Get list of pending segment indices"""
        all_segments = set(range(self.total_segments))
        processed = set(self.completed_segments) | set(self.failed_segments)
        return sorted(list(all_segments - processed))
    
    @property
    def duration_seconds(self) -> float:
        """Calculate job duration in seconds"""
        end_time = self.completed_at or self.updated_at
        return (end_time - self.started_at).total_seconds()
    
    def mark_segment_completed(self, segment_index: int) -> None:
        """Mark a segment as completed"""
        if segment_index not in self.completed_segments:
            self.completed_segments.append(segment_index)
        if segment_index in self.failed_segments:
            self.failed_segments.remove(segment_index)
        self.updated_at = datetime.now()
    
    def mark_segment_failed(self, segment_index: int) -> None:
        """Mark a segment as failed"""
        if segment_index not in self.failed_segments:
            self.failed_segments.append(segment_index)
        if segment_index in self.completed_segments:
            self.completed_segments.remove(segment_index)
        self.updated_at = datetime.now()
    
    def advance_stage(self, new_stage: ProcessingStage) -> None:
        """Advance to next processing stage"""
        self.stage = new_stage
        self.updated_at = datetime.now()
        if new_stage == ProcessingStage.COMPLETED:
            self.completed_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "job_id": self.job_id,
            "input_file": str(self.input_file),
            "output_dir": str(self.output_dir),
            "stage": self.stage.value,
            "total_segments": self.total_segments,
            "completed_segments": self.completed_segments,
            "failed_segments": self.failed_segments,
            "audio_chunks": self.audio_chunks,
            "config_snapshot": self.config_snapshot,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "JobState":
        """Create from dictionary"""
        data = data.copy()
        
        # Convert paths
        if "input_file" in data:
            data["input_file"] = Path(data["input_file"])
        if "output_dir" in data:
            data["output_dir"] = Path(data["output_dir"])
        
        # Convert stage
        if "stage" in data and isinstance(data["stage"], str):
            data["stage"] = ProcessingStage(data["stage"])
        
        # Convert timestamps
        for field_name in ["started_at", "updated_at", "completed_at"]:
            if field_name in data and data[field_name] and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)
