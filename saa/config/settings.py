"""
Settings management using Pydantic with environment variable support
"""
import os
from pathlib import Path
from typing import Optional, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv


# Find project root (where .env is located)
def find_project_root() -> Path:
    """Find the project root directory by looking for .env file"""
    current = Path(__file__).resolve().parent  # Start from saa/config/
    
    # Walk up the directory tree looking for .env
    for parent in [current, *current.parents]:
        env_file = parent / ".env"
        if env_file.exists():
            return parent
    
    # Fallback: assume .env is 2 levels up from this file (saa/config/ -> saa/ -> root/)
    return current.parent.parent


PROJECT_ROOT = find_project_root()
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Load .env file explicitly using dotenv
load_dotenv(dotenv_path=ENV_FILE_PATH)


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),  # Explicit absolute path to .env
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Google API Configuration
    google_api_key: str = Field(..., description="Google API key for ADK agents")
    gemini_text_model: str = Field(
        default="gemini-2.0-flash-lite",
        description="Gemini model for text agents"
    )
    gemini_pro_model: str = Field(
        default="gemini-2.0-flash",
        description="Gemini pro model for complex tasks"
    )
    
    # Replicate Configuration (TTS only)
    replicate_api_token: Optional[str] = Field(
        default=None,
        description="Replicate API token (optional - falls back to local TTS)"
    )
    
    # LLM Provider Configuration (for agents, NOT TTS)
    llm_provider: Literal["gemini", "ollama", "openrouter"] = Field(
        default="gemini",
        description="LLM provider for agents (gemini|ollama|openrouter)"
    )
    
    # Ollama Configuration (local LLM)
    ollama_model: str = Field(
        default="mistral-small3.1",
        description="Ollama model name (e.g., mistral-small3.1, llama3.1)"
    )
    ollama_api_base: Optional[str] = Field(
        default=None,
        description="Ollama API base URL (defaults to http://localhost:11434)"
    )
    ollama_api_key: Optional[str] = Field(
        default="placeholder",
        description="Ollama API key placeholder (not needed for local, reserved for future cloud Ollama)"
    )
    
    # OpenRouter Configuration (cloud LLM)
    openrouter_model: str = Field(
        default="anthropic/claude-3.5-sonnet",
        description="OpenRouter model ID (e.g., anthropic/claude-3.5-sonnet, google/gemini-2.5-flash)"
    )
    openrouter_api_key: Optional[str] = Field(
        default=None,
        description="OpenRouter API key (required if using OpenRouter)"
    )
    
    # Session Management
    session_db_path: Optional[str] = Field(
        default="./sessions.db",
        description="Path to SQLite database for persistent sessions"
    )
    
    # TTS Provider
    tts_provider: Literal["auto", "replicate", "local"] = Field(
        default="auto",
        description="TTS provider selection"
    )
    
    # Output Configuration
    output_dir: Path = Field(default=Path("./output"), description="Output directory")
    temp_dir: Path = Field(default=Path("./output/.temp"), description="Temporary audio chunks")
    sample_dir: Path = Field(default=Path("./samples"), description="Sample directory")
    
    # Session & Checkpoint
    session_db_path: Path = Field(
        default=Path("./saa_sessions.db"),
        description="SQLite database for sessions"
    )
    checkpoint_interval: int = Field(
        default=10,
        ge=1,
        description="Save checkpoint every N segments"
    )
    use_msgpack: bool = Field(
        default=True,
        description="Use MessagePack for checkpoints"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_json: bool = Field(default=False, description="JSON logging format")
    log_dir: Path = Field(default=Path("./logs"), description="Log directory")
    
    # GPU Configuration
    use_gpu: bool = Field(default=True, description="Enable GPU acceleration")
    gpu_id: int = Field(default=0, ge=0, description="GPU device ID")
    
    # Audio Configuration
    default_voice_profile: str = Field(default="narrator", description="Default voice")
    default_language: str = Field(default="en", description="Default language")
    default_audio_format: Literal["mp3", "wav", "ogg", "flac"] = Field(
        default="mp3",
        description="Default output audio format"
    )
    audio_quality: Literal["low", "medium", "high"] = Field(
        default="high",
        description="Audio quality preset"
    )
    
    # TTS Quality Settings
    tts_temperature: float = Field(
        default=0.75,
        ge=0.1,
        le=1.0,
        description="TTS temperature (expressiveness)"
    )
    tts_repetition_penalty: float = Field(
        default=7.0,
        ge=1.0,
        description="Repetition penalty"
    )
    tts_speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Playback speed multiplier"
    )
    
    # Text Processing
    max_segment_length: int = Field(
        default=250,
        ge=100,
        le=1000,
        description="Maximum segment length"
    )
    chunk_size: int = Field(
        default=500,
        ge=100,
        description="Characters per chunk"
    )
    sample_paragraphs: int = Field(
        default=3,
        ge=1,
        description="Paragraphs for sample generation"
    )
    
    # Reference Audio
    reference_audio_dir: Path = Field(
        default=Path("./reference_audio"),
        description="Reference audio directory"
    )
    default_male_voice: str = Field(
        default="male.wav",
        description="Default male voice file"
    )
    default_female_voice: str = Field(
        default="female.wav",
        description="Default female voice file"
    )
    
    @field_validator("output_dir", "sample_dir", "log_dir", "reference_audio_dir", "temp_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist"""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("google_api_key")
    @classmethod
    def validate_google_api_key(cls, v: str) -> str:
        """Validate Google API key is not placeholder"""
        if not v or v == "your_google_api_key_here":
            raise ValueError(
                "GOOGLE_API_KEY must be set in .env file. "
                "Get your key from https://makersuite.google.com/app/apikey"
            )
        return v
    
    @property
    def has_replicate_token(self) -> bool:
        """Check if Replicate token is configured"""
        return bool(
            self.replicate_api_token 
            and self.replicate_api_token != "your_replicate_token_here"
        )
    
    @property
    def effective_tts_provider(self) -> Literal["replicate", "local"]:
        """Determine actual TTS provider to use"""
        if self.tts_provider == "auto":
            return "replicate" if self.has_replicate_token else "local"
        elif self.tts_provider == "replicate" and not self.has_replicate_token:
            return "local"  # Fallback
        return self.tts_provider
    
    @property
    def male_voice_path(self) -> Path:
        """Get full path to male voice reference"""
        return self.reference_audio_dir / self.default_male_voice
    
    @property
    def female_voice_path(self) -> Path:
        """Get full path to female voice reference"""
        return self.reference_audio_dir / self.default_female_voice


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Call this instead of instantiating Settings directly.
    
    Note: .env is already loaded via load_dotenv() at module import.
    """
    return Settings()
