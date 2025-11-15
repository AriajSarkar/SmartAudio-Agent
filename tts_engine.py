"""
TTS Engine Module using Coqui TTS XTTS-v2
"""
import torch
from TTS.api import TTS
from pathlib import Path
from typing import Optional, List
import numpy as np
from config import TTS_CONFIG, GPU_CONFIG, EMOTION_CONFIG

# Optional emotion controller (only loaded if enabled)
emotion_controller = None
if EMOTION_CONFIG.get('enabled', False):
    try:
        from emotion_controller import EmotionController
        if Path(EMOTION_CONFIG['config_file']).exists():
            emotion_controller = EmotionController(EMOTION_CONFIG['config_file'])
            print("✓ Emotion control enabled")
    except ImportError:
        print("⚠ Emotion controller not available")


class TTSEngine:
    """High-quality TTS using Coqui XTTS-v2"""
    
    def __init__(self):
        self.model = None
        self.device = self._setup_device()
        self.model_name = TTS_CONFIG['model_name']
        self.emotion_controller = emotion_controller
        
    def _setup_device(self) -> str:
        """Configure GPU/CPU device"""
        if GPU_CONFIG['use_gpu'] and torch.cuda.is_available():
            device = f"cuda:{GPU_CONFIG['gpu_id']}"
            print(f"✓ Using GPU: {torch.cuda.get_device_name(0)}")
            print(f"✓ VRAM Available: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            return device
        else:
            print("⚠ Using CPU (this will be slower)")
            return "cpu"
    
    def initialize(self):
        """Load TTS model"""
        if self.model is None:
            print(f"Loading TTS model: {self.model_name}")
            print("(First time will download ~2GB model...)")
            
            self.model = TTS(self.model_name).to(self.device)
            
            print("✓ Model loaded successfully!")
            
            # Print available speakers if using multi-speaker model
            if hasattr(self.model, 'speakers') and self.model.speakers:
                print(f"✓ Available speakers: {len(self.model.speakers)}")
            
            # For XTTS models, we'll use the built-in speaker samples
            # XTTS doesn't have predefined speakers, it uses voice cloning
    
    def generate_speech(
        self,
        text: str,
        output_path: str,
        speaker_wav: Optional[str] = None,
        language: str = None,
        use_emotion: bool = True
    ) -> str:
        """
        Generate speech from text with optional emotion control
        
        Args:
            text: Input text
            output_path: Where to save audio file
            speaker_wav: Path to reference audio for voice cloning
            language: Language code (default from config)
            use_emotion: Whether to use emotion detection (default True if enabled)
        
        Returns:
            Path to generated audio file
        """
        if self.model is None:
            self.initialize()
        
        language = language or TTS_CONFIG['language']
        
        # Check if emotion control should override speaker_wav
        emotion_ref_audio = None
        if use_emotion and self.emotion_controller:
            # Process text for emotions
            emotion_chunks = self.emotion_controller.process_text_with_emotions(text)
            # Use the first chunk's emotion reference (if available)
            if emotion_chunks and emotion_chunks[0]['reference_audio']:
                emotion_ref_audio = emotion_chunks[0]['reference_audio']
                if Path(emotion_ref_audio).exists():
                    print(f"  Using {emotion_chunks[0]['emotion']} voice: {emotion_ref_audio}")
                    speaker_wav = emotion_ref_audio
        
        # Fallback to default speaker_wav
        if not speaker_wav:
            speaker_wav = TTS_CONFIG['speaker_wav']
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Generate speech
            # XTTS model requires either speaker_wav for voice cloning
            # or we use the model's reference audio samples
            if speaker_wav and Path(speaker_wav).exists():
                # Voice cloning mode with user-provided audio
                print(f"  Generating with voice cloning from: {speaker_wav}")
                self.model.tts_to_file(
                    text=text,
                    file_path=str(output_path),
                    speaker_wav=speaker_wav,
                    language=language,
                    **self._get_generation_params()
                )
            else:
                # XTTS requires a reference audio. Since user hasn't provided one,
                # give helpful instructions
                raise RuntimeError(
                    "XTTS model requires a reference audio (speaker_wav).\n\n"
                    "Quick Fix:\n"
                    "1. Download free sample: Run 'python download_reference_audio.py'\n"
                    "2. Or record 6-10 seconds of any clear speech and save as WAV\n"
                    "3. Update config.py with the path:\n"
                    "   TTS_CONFIG = {'speaker_wav': 'path/to/audio.wav'}\n\n"
                    "Free audio sources:\n"
                    "  - https://freesound.org/ (search 'voice sample')\n"
                    "  - Record your own voice with Windows Voice Recorder\n"
                    "  - Use any audiobook/podcast sample (6+ seconds)"
                )
            
            return str(output_path)
        
        except Exception as e:
            raise RuntimeError(f"TTS generation failed: {str(e)}")
    
    def _get_generation_params(self) -> dict:
        """Get generation parameters from config"""
        params = {}
        
        # Only include parameters that the model supports
        supported_params = ['temperature', 'length_penalty', 'repetition_penalty', 
                          'top_k', 'top_p', 'speed']
        
        for param in supported_params:
            if param in TTS_CONFIG:
                params[param] = TTS_CONFIG[param]
        
        return params
    
    def generate_batch(
        self,
        texts: List[str],
        output_dir: str,
        base_filename: str = "chunk",
        speaker_wav: Optional[str] = None,
        language: str = None,
        progress_callback=None
    ) -> List[str]:
        """
        Generate speech for multiple text chunks
        
        Args:
            texts: List of text chunks
            output_dir: Directory to save chunks
            base_filename: Base name for chunk files
            speaker_wav: Reference audio for voice cloning
            language: Language code
            progress_callback: Function to call with progress updates
        
        Returns:
            List of generated file paths
        """
        if self.model is None:
            self.initialize()
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        for i, text in enumerate(texts):
            output_path = output_dir / f"{base_filename}_{i:04d}.wav"
            
            if progress_callback:
                progress_callback(i, len(texts), text[:50])
            
            try:
                self.generate_speech(
                    text=text,
                    output_path=str(output_path),
                    speaker_wav=speaker_wav,
                    language=language
                )
                generated_files.append(str(output_path))
            
            except Exception as e:
                print(f"✗ Error generating chunk {i}: {str(e)}")
                continue
        
        return generated_files
    
    def cleanup(self):
        """Free GPU memory"""
        if self.model is not None:
            del self.model
            self.model = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("✓ GPU memory cleared")
    
    def get_info(self) -> dict:
        """Get model and device information"""
        info = {
            'model': self.model_name,
            'device': self.device,
            'language': TTS_CONFIG['language'],
        }
        
        if torch.cuda.is_available() and self.device.startswith('cuda'):
            info['gpu_name'] = torch.cuda.get_device_name(0)
            info['vram_total_gb'] = torch.cuda.get_device_properties(0).total_memory / 1024**3
            if self.model is not None:
                info['vram_allocated_gb'] = torch.cuda.memory_allocated(0) / 1024**3
        
        return info
