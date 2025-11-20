"""
Immutable constants for SAA system
"""
from typing import Final

# TTS Model Limits
MAX_SEGMENT_LENGTH: Final[int] = 250  # Characters per TTS segment (actual XTTS-v2 limit for quality)
SAFE_SEGMENT_LENGTH: Final[int] = 200  # Safe threshold with margin (prevents truncation warnings)
MIN_SEGMENT_LENGTH: Final[int] = 50  # Minimum viable segment

# Supported File Formats
SUPPORTED_INPUT_FORMATS: Final[tuple] = ('.pdf', '.txt')
SUPPORTED_AUDIO_FORMATS: Final[tuple] = ('mp3', 'wav', 'ogg', 'flac')

# Audio Processing
DEFAULT_SAMPLE_RATE: Final[int] = 24000  # Hz (XTTS-v2 output)
DEFAULT_CHANNELS: Final[int] = 1  # Mono
CROSSFADE_DURATION: Final[int] = 100  # Milliseconds

# TTS Quality Settings for Human-Like Audio (optimized for short segments)
TTS_BASE_TEMPERATURE: Final[float] = 0.85  # Higher for expressiveness in short segments
TTS_BASE_REPETITION_PENALTY: Final[float] = 10.0  # Prevent word repetition
TTS_SPEED_VARIANCE: Final[float] = 0.05  # Subtle speed variation for naturalness
TTS_ENABLE_PROSODY_ENHANCEMENT: Final[bool] = True  # Enable enhanced intonation

# Voice Reference Requirements
MIN_REFERENCE_DURATION: Final[float] = 6.0  # Seconds
MAX_REFERENCE_DURATION: Final[float] = 15.0  # Seconds
RECOMMENDED_REFERENCE_DURATION: Final[float] = 10.0  # Seconds

# Processing Limits
MAX_PARALLEL_SYNTHESIS: Final[int] = 3  # GPU memory constraint (RTX 3050 4GB)
DEFAULT_BATCH_SIZE: Final[int] = 10  # Segments per batch
MAX_RETRIES: Final[int] = 3  # API retry attempts

# Timeouts (seconds)
TTS_TIMEOUT: Final[int] = 300  # 5 minutes per segment
API_TIMEOUT: Final[int] = 30  # API request timeout
CHECKPOINT_SAVE_INTERVAL: Final[int] = 10  # Save every N segments

# File Naming Patterns
CHUNK_FILE_PATTERN: Final[str] = "chunk_{index:04d}.wav"
TEMP_DIR_NAME: Final[str] = ".temp"
MERGED_FILE_NAME: Final[str] = "merged.wav"
NORMALIZED_FILE_NAME: Final[str] = "normalized.wav"
SAMPLE_FILE_PATTERN: Final[str] = "sample_{timestamp}.wav"
AUDIOBOOK_FILE_PATTERN: Final[str] = "{name}_audiobook_{timestamp}.{format}"
CHARACTER_AUDIOBOOK_PATTERN: Final[str] = "{name}_character_voices_{timestamp}.{format}"
CHECKPOINT_FILE: Final[str] = "checkpoint.msgpack"
JOB_STATE_FILE: Final[str] = "job_state.msgpack"
LOG_FILE: Final[str] = "pipeline.log"

# Character Detection Patterns
DIALOGUE_ATTRIBUTION_PATTERNS: Final[tuple] = (
    r'said\s+(\w+)',
    r'(\w+)\s+said',
    r'(\w+)\s+replied',
    r'replied\s+(\w+)',
    r'(\w+)\s+asked',
    r'asked\s+(\w+)',
    r'(\w+)\s+shouted',
    r'shouted\s+(\w+)',
    r'(\w+)\s+whispered',
    r'whispered\s+(\w+)',
)

# Gender Keywords
FEMININE_PRONOUNS: Final[set] = {'she', 'her', 'hers', 'herself'}
MASCULINE_PRONOUNS: Final[set] = {'he', 'him', 'his', 'himself'}

# Spinner Animation
SPINNER_CHARS: Final[tuple] = ('⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏')
SPINNER_INTERVAL: Final[float] = 0.1  # Seconds

# GPU Memory
GPU_MEMORY_WARNING_THRESHOLD: Final[float] = 0.9  # 90% VRAM usage
GPU_MEMORY_CRITICAL_THRESHOLD: Final[float] = 0.95  # 95% VRAM usage

# Job States
class JobState:
    """Job state constants"""
    PENDING: Final[str] = "pending"
    PROCESSING: Final[str] = "processing"
    COMPLETED: Final[str] = "completed"
    FAILED: Final[str] = "failed"
    CANCELLED: Final[str] = "cancelled"
    PAUSED: Final[str] = "paused"

# Processing Steps
class ProcessingStep:
    """Pipeline step constants"""
    DOCUMENT_LOAD: Final[str] = "document_load"
    TEXT_CLEANING: Final[str] = "text_cleaning"
    SEGMENTATION: Final[str] = "segmentation"
    VOICE_PLANNING: Final[str] = "voice_planning"
    SYNTHESIS: Final[str] = "synthesis"
    AUDIO_MERGE: Final[str] = "audio_merge"
    FINALIZATION: Final[str] = "finalization"
