"""
TTS synthesis tools (ADK function tools)
Orchestrate Replicate and local TTS providers with fallback
"""
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from saa.providers import LocalTTSProvider, ReplicateTTSProvider
from saa.exceptions import ReplicateAuthError, ReplicateAPIError, GPUOutOfMemoryError
from saa.config import get_settings

logger = logging.getLogger(__name__)

# Module-level provider instances (lazy-initialized)
_local_provider: Optional[LocalTTSProvider] = None
_replicate_provider: Optional[ReplicateTTSProvider] = None


def synthesize_with_replicate(
    text: str,
    output_path: str,
    voice: str = "neutral",
    reference_audio: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesize speech using Replicate cloud API.
    
    Cloud-based TTS synthesis without local GPU requirements.
    Requires REPLICATE_API_TOKEN in environment. If token missing
    or API fails, returns error status to trigger local fallback.
    
    Args:
        text: Text to synthesize
        output_path: Path for output audio file
        voice: Voice preset name
        reference_audio: Optional reference audio (model-dependent)
    
    Returns:
        Dictionary with:
            - status: "success", "error", or "fallback_required"
            - output_file: Path to generated audio
            - file_size_mb: Audio file size
            - synthesis_method: "replicate"
            - error: Error message if failed
    """
    global _replicate_provider
    
    try:
        settings = get_settings()
        
        # Check if Replicate token is configured
        if not settings.has_replicate_token:
            logger.warning("Replicate token not configured, fallback required")
            return {
                "status": "fallback_required",
                "output_file": "",
                "error": "REPLICATE_API_TOKEN not set in environment",
                "synthesis_method": "replicate"
            }
        
        # Initialize provider if needed
        if _replicate_provider is None:
            _replicate_provider = ReplicateTTSProvider(
                api_token=settings.replicate_api_token
            )
        
        # Attempt synthesis
        result = _replicate_provider.synthesize(
            text=text,
            output_path=output_path,
            voice=voice
        )
        
        return result
    
    except (ReplicateAuthError, ReplicateAPIError) as e:
        logger.warning(f"Replicate API error: {str(e)}, falling back to local")
        return {
            "status": "fallback_required",
            "output_file": "",
            "error": str(e),
            "synthesis_method": "replicate"
        }
    
    except Exception as e:
        logger.error(f"Unexpected Replicate error: {str(e)}")
        return {
            "status": "error",
            "output_file": "",
            "error": str(e),
            "synthesis_method": "replicate"
        }


def synthesize_with_local(
    text: str,
    output_path: str,
    reference_audio: str,
    language: str = "en",
    temperature: float = 0.75,
    speed: float = 1.0
) -> Dict[str, Any]:
    """
    Synthesize speech using local Coqui XTTS-v2 model.
    
    High-quality voice cloning using local GPU. Requires reference
    audio (6-15 seconds) for voice cloning. Manages GPU memory
    automatically.
    
    Args:
        text: Text to synthesize (max 800 chars)
        output_path: Path for output audio file  
        reference_audio: Path to voice reference audio (WAV, 6-15s)
        language: Language code (en, es, fr, etc.)
        temperature: Expressiveness (0.1-1.0)
        speed: Playback speed multiplier (0.5-2.0)
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - output_file: Path to generated audio
            - file_size_mb: Audio file size
            - synthesis_method: "local_xtts"
            - error: Error message if failed
    """
    global _local_provider
    
    try:
        settings = get_settings()
        
        # Initialize provider if needed
        if _local_provider is None:
            _local_provider = LocalTTSProvider(
                use_gpu=settings.use_gpu,
                gpu_id=settings.gpu_id
            )
        
        # Synthesize
        result = _local_provider.synthesize(
            text=text,
            output_path=output_path,
            reference_audio=reference_audio,
            language=language,
            temperature=temperature,
            speed=speed,
            repetition_penalty=settings.tts_repetition_penalty
        )
        
        return result
    
    except GPUOutOfMemoryError as e:
        logger.error(f"GPU OOM: {str(e)}")
        # Cleanup and retry could be implemented here
        _local_provider.cleanup()
        return {
            "status": "error",
            "output_file": "",
            "error": f"GPU out of memory: {str(e)}. Try reducing batch size.",
            "synthesis_method": "local_xtts"
        }
    
    except Exception as e:
        logger.error(f"Local TTS error: {str(e)}")
        return {
            "status": "error",
            "output_file": "",
            "error": str(e),
            "synthesis_method": "local_xtts"
        }


def synthesize_audio(
    text: str,
    output_path: str,
    reference_audio: str,
    provider: str = "auto",
    voice: str = "neutral",
    language: str = "en",
    temperature: float = 0.75,
    speed: float = 1.0,
    use_temp_dir: bool = True
) -> Dict[str, Any]:
    """
    Synthesize speech with automatic provider selection and fallback.
    
    Intelligently chooses between Replicate (cloud) and local XTTS
    based on configuration and availability. Falls back to local
    if Replicate fails.
    
    Args:
        text: Text to synthesize
        output_path: Path for output audio (if use_temp_dir=True, saved to temp_dir)
        reference_audio: Voice reference audio path
        provider: "auto", "replicate", or "local"
        voice: Voice preset (for Replicate)
        language: Language code
        temperature: Expressiveness
        speed: Playback speed
        use_temp_dir: Save chunks to temp directory (cleaned after merge)
    
    Returns:
        Dictionary with synthesis result and method used
    """
    # Override output_path to use temp directory for chunks
    if use_temp_dir:
        settings = get_settings()
        # Ensure temp_dir is absolute
        if not settings.temp_dir.is_absolute():
            temp_dir = Path.cwd() / settings.temp_dir
        else:
            temp_dir = settings.temp_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Preserve subdirectory structure (e.g., voices/chunk_0000.wav)
        output_path_obj = Path(output_path)
        if len(output_path_obj.parts) > 1:
            # Has subdirectory (e.g., "voices/chunk_0000.wav")
            subdir = output_path_obj.parent
            filename = output_path_obj.name
            full_output_dir = temp_dir / subdir
            full_output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(full_output_dir / filename)
        else:
            # Just filename (e.g., "chunk_0000.wav")
            output_filename = output_path_obj.name
            output_path = str(temp_dir / output_filename)
        
        logger.info(f"[TTS] Redirecting output to temp_dir: {output_path}")
    else:
        logger.info(f"[TTS] Using direct output path: {output_path}")
    
    original_settings = get_settings()
    
    # Determine provider
    if provider == "auto":
        provider = original_settings.effective_tts_provider
    
    # Try Replicate first if selected
    if provider == "replicate":
        logger.info("Attempting Replicate synthesis...")
        result = synthesize_with_replicate(
            text=text,
            output_path=output_path,
            voice=voice,
            reference_audio=reference_audio
        )
        
        # If successful, return
        if result["status"] == "success":
            return result
        
        # If fallback required, try local
        if result["status"] == "fallback_required":
            logger.info("Falling back to local TTS...")
            provider = "local"
        else:
            # Hard error, return it
            return result
    
    # Use local TTS
    if provider == "local":
        logger.info("Using local XTTS synthesis...")
        result = synthesize_with_local(
            text=text,
            output_path=output_path,
            reference_audio=reference_audio,
            language=language,
            temperature=temperature,
            speed=speed
        )
        return result
    
    # Should not reach here
    return {
        "status": "error",
        "output_file": "",
        "error": f"Invalid provider: {provider}",
        "synthesis_method": "unknown"
    }


def cleanup_tts_resources() -> Dict[str, Any]:
    """
    Free TTS provider resources (especially GPU memory).
    
    Call this after completing a batch of synthesis to release
    GPU memory. Important for long-running jobs.
    
    Returns:
        Dictionary with cleanup status
    """
    global _local_provider, _replicate_provider
    
    cleaned = []
    
    if _local_provider is not None:
        _local_provider.cleanup()
        _local_provider = None
        cleaned.append("local_provider")
    
    if _replicate_provider is not None:
        _replicate_provider = None
        cleaned.append("replicate_provider")
    
    logger.info(f"Cleaned up TTS resources: {cleaned}")
    
    return {
        "status": "success",
        "cleaned_resources": cleaned
    }
