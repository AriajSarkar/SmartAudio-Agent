"""
Local TTS Provider using Coqui XTTS-v2
Migrated from legacy tts_engine.py with improvements
"""
import torch
from TTS.api import TTS
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from saa.exceptions import LocalTTSError, VoiceReferenceError, GPUOutOfMemoryError
from saa.constants import MAX_SEGMENT_LENGTH

logger = logging.getLogger(__name__)


class LocalTTSProvider:
    """
    Local TTS synthesis using Coqui XTTS-v2 model
    
    Provides high-quality voice cloning with GPU acceleration.
    Automatically manages GPU memory and handles cleanup.
    """
    
    def __init__(
        self,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        use_gpu: bool = True,
        gpu_id: int = 0
    ):
        self.model_name = model_name
        self.model = None
        self.device = self._setup_device(use_gpu, gpu_id)
        logger.info(f"LocalTTSProvider initialized on device: {self.device}")
    
    def _setup_device(self, use_gpu: bool, gpu_id: int) -> str:
        """Configure GPU/CPU device"""
        if use_gpu and torch.cuda.is_available():
            device = f"cuda:{gpu_id}"
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"Using GPU: {gpu_name} ({vram_gb:.2f} GB VRAM)")
            return device
        else:
            logger.warning("Using CPU (slower than GPU)")
            return "cpu"
    
    def initialize(self) -> None:
        """Load TTS model into memory"""
        if self.model is not None:
            logger.debug("Model already loaded")
            return
        
        try:
            logger.info(f"Loading TTS model: {self.model_name}")
            logger.info("First run will download ~2GB model from Coqui...")
            
            self.model = TTS(self.model_name).to(self.device)
            
            logger.info("✓ Model loaded successfully")
            
        except Exception as e:
            raise LocalTTSError(f"Failed to load TTS model: {str(e)}")
    
    def synthesize(
        self,
        text: str,
        output_path: str,
        reference_audio: str,
        language: str = "en",
        temperature: float = 0.75,
        repetition_penalty: float = 7.0,
        speed: float = 1.0
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text using voice cloning.
        
        Args:
            text: Text to synthesize (max 800 chars for XTTS-v2)
            output_path: Where to save generated audio
            reference_audio: Path to voice reference audio (6-15s WAV)
            language: Language code (en, es, fr, etc.)
            temperature: Expressiveness (0.1-1.0, higher = more expressive)
            repetition_penalty: Prevent word loops (higher = less repetition)
            speed: Playback speed multiplier
        
        Returns:
            Dict with status, output_file, duration, error
        """
        try:
            # Validate inputs
            if len(text) > MAX_SEGMENT_LENGTH:
                raise LocalTTSError(
                    f"Text too long: {len(text)} chars (max {MAX_SEGMENT_LENGTH})"
                )
            
            ref_path = Path(reference_audio)
            if not ref_path.exists():
                raise VoiceReferenceError(
                    f"Reference audio not found: {reference_audio}",
                    str(ref_path)
                )
            
            # Initialize model if needed
            if self.model is None:
                self.initialize()
            
            # Prepare output path
            output_path_obj = Path(output_path)
            
            # If path is already absolute (e.g., from temp_dir), use it as-is
            # Otherwise, ensure it's in ./output/ directory
            if not output_path_obj.is_absolute():
                output_path_obj = Path.cwd() / "output" / output_path_obj.name
            
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Check GPU memory before generation
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(0) / 1024**3
                max_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
                
                if allocated / max_mem > 0.9:  # 90% threshold
                    logger.warning(f"High GPU memory usage: {allocated:.2f}/{max_mem:.2f} GB")
                    # Try cleanup
                    torch.cuda.empty_cache()
            
            # Generate speech
            logger.debug(f"Synthesizing {len(text)} chars with {ref_path.name}")
            
            try:
                self.model.tts_to_file(
                    text=text,
                    file_path=str(output_path_obj),
                    speaker_wav=str(ref_path),
                    language=language,
                    temperature=temperature,
                    repetition_penalty=repetition_penalty,
                    speed=speed
                )
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    allocated = torch.cuda.memory_allocated(0) / 1024**3
                    max_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
                    raise GPUOutOfMemoryError(allocated, max_mem)
                raise
            
            # Get file size for validation
            file_size_mb = output_path_obj.stat().st_size / (1024 * 1024)
            
            logger.info(f"✓ Generated {file_size_mb:.2f} MB audio")
            
            return {
                "status": "success",
                "output_file": str(output_path_obj),
                "file_size_mb": round(file_size_mb, 2),
                "synthesis_method": "local_xtts",
                "error": None
            }
        
        except GPUOutOfMemoryError:
            raise  # Re-raise for agent to handle
        
        except Exception as e:
            logger.error(f"Synthesis failed: {str(e)}")
            return {
                "status": "error",
                "output_file": "",
                "error": str(e),
                "synthesis_method": "local_xtts"
            }
    
    def cleanup(self) -> None:
        """Free GPU memory"""
        if self.model is not None:
            del self.model
            self.model = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("✓ GPU memory cleared")
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information"""
        info = {
            "provider": "local_xtts",
            "model": self.model_name,
            "device": self.device,
            "model_loaded": self.model is not None
        }
        
        if torch.cuda.is_available() and self.device.startswith('cuda'):
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["vram_total_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / 1024**3, 2
            )
            if self.model is not None:
                info["vram_allocated_gb"] = round(
                    torch.cuda.memory_allocated(0) / 1024**3, 2
                )
        
        return info
    
    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()
