"""
Custom exceptions for SAA system
Extends ADK exceptions where appropriate
"""
from typing import Optional, Dict, Any


class SAAError(Exception):
    """Base exception for all SAA errors"""
    
    def __init__(
        self,
        message: str,
        code: str = "SAA_ERROR",
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = False
    ):
        self.message = message
        self.code = code
        self.context = context or {}
        self.recoverable = recoverable
        super().__init__(self.message)
    
    def __str__(self) -> str:
        context_str = f" | Context: {self.context}" if self.context else ""
        return f"[{self.code}] {self.message}{context_str}"


class DocumentError(SAAError):
    """Document processing errors"""
    def __init__(self, message: str, **kwargs):
        kwargs.pop('code', None)
        super().__init__(message, code="DOC_ERROR", **kwargs)


class FileNotFoundError(DocumentError):
    """File not found error"""
    def __init__(self, file_path: str):
        super().__init__(
            f"File not found: {file_path}",
            code="FILE_NOT_FOUND",
            context={"file_path": file_path}
        )


class UnsupportedFormatError(DocumentError):
    """Unsupported file format"""
    def __init__(self, format: str, supported: tuple):
        super().__init__(
            f"Unsupported format: {format}. Supported: {', '.join(supported)}",
            code="UNSUPPORTED_FORMAT",
            context={"format": format, "supported": list(supported)}
        )


class TextProcessingError(SAAError):
    """Text processing errors"""
    def __init__(self, message: str, **kwargs):
        kwargs.pop('code', None)
        super().__init__(message, code="TEXT_ERROR", **kwargs)


class SegmentTooLongError(TextProcessingError):
    """Segment exceeds maximum length"""
    def __init__(self, length: int, max_length: int):
        super().__init__(
            f"Segment too long: {length} chars (max: {max_length})",
            code="SEGMENT_TOO_LONG",
            context={"length": length, "max_length": max_length},
            recoverable=True  # Can retry with smaller chunks
        )


class GPUError(SAAError):
    """GPU-related errors"""
    def __init__(self, message: str, **kwargs):
        kwargs.pop('code', None)
        super().__init__(message, code="GPU_ERROR", **kwargs)


class GPUOutOfMemoryError(GPUError):
    """GPU out of memory"""
    def __init__(self, allocated: float, max_memory: float):
        super().__init__(
            f"GPU OOM: {allocated:.2f}GB / {max_memory:.2f}GB",
            code="GPU_OOM",
            context={"allocated_gb": allocated, "max_gb": max_memory},
            recoverable=True  # Can retry with smaller batch or CPU fallback
        )


class TTSError(SAAError):
    """TTS synthesis errors"""
    def __init__(self, message: str, **kwargs):
        # Extract code if present in kwargs to avoid conflict
        kwargs.pop('code', None)
        super().__init__(message, code="TTS_ERROR", **kwargs)


class VoiceReferenceError(TTSError):
    """Invalid voice reference audio"""
    def __init__(self, message: str, file_path: Optional[str] = None):
        context = {"file_path": file_path} if file_path else {}
        super().__init__(
            message,
            code="INVALID_VOICE_REF",
            context=context
        )


class LocalTTSError(TTSError):
    """Local TTS provider errors"""
    def __init__(self, message: str, **kwargs):
        # Extract code if present in kwargs to avoid conflict
        kwargs.pop('code', None)
        super().__init__(message, code="LOCAL_TTS_ERROR", **kwargs)


class ReplicateError(SAAError):
    """Replicate API errors"""
    def __init__(self, message: str, **kwargs):
        kwargs.pop('code', None)
        super().__init__(message, code="REPLICATE_ERROR", **kwargs)


class ReplicateAuthError(ReplicateError):
    """Replicate authentication failed"""
    def __init__(self):
        super().__init__(
            "Replicate API token missing or invalid",
            code="REPLICATE_AUTH_ERROR",
            recoverable=True  # Can fallback to local TTS
        )


class ReplicateAPIError(ReplicateError):
    """Replicate API request failed"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        context = {"status_code": status_code} if status_code else {}
        super().__init__(
            message,
            code="REPLICATE_API_ERROR",
            context=context,
            recoverable=True  # Can retry or fallback
        )


class AudioProcessingError(SAAError):
    """Audio processing errors"""
    def __init__(self, message: str, **kwargs):
        kwargs.pop('code', None)
        super().__init__(message, code="AUDIO_ERROR", **kwargs)


class AudioMergeError(AudioProcessingError):
    """Audio merge failed"""
    def __init__(self, message: str, **kwargs):
        kwargs.pop('code', None)
        super().__init__(message, code="AUDIO_MERGE_ERROR", **kwargs)


class CheckpointError(SAAError):
    """Checkpoint/resume errors"""
    def __init__(self, message: str, **kwargs):
        kwargs.pop('code', None)
        super().__init__(message, code="CHECKPOINT_ERROR", **kwargs)


class CheckpointCorruptedError(CheckpointError):
    """Checkpoint file corrupted"""
    def __init__(self, file_path: str):
        super().__init__(
            f"Checkpoint corrupted: {file_path}",
            code="CHECKPOINT_CORRUPTED",
            context={"file_path": file_path}
        )


class CheckpointNotFoundError(CheckpointError):
    """Checkpoint not found"""
    def __init__(self, job_id: str):
        super().__init__(
            f"No checkpoint found for job: {job_id}",
            code="CHECKPOINT_NOT_FOUND",
            context={"job_id": job_id}
        )


class ConfigurationError(SAAError):
    """Configuration errors"""
    def __init__(self, message: str, **kwargs):
        kwargs.pop('code', None)
        super().__init__(message, code="CONFIG_ERROR", **kwargs)


class ValidationError(SAAError):
    """Input validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        context = {"field": field} if field else {}
        super().__init__(message, code="VALIDATION_ERROR", context=context, **kwargs)
