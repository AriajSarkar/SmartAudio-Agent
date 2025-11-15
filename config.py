"""
Configuration settings for AudioBook TTS System
"""
import os
from pathlib import Path

# Project Paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
SAMPLE_DIR = BASE_DIR / "samples"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
SAMPLE_DIR.mkdir(exist_ok=True)

# TTS Settings
TTS_CONFIG = {
    # Model selection
    "model_name": "tts_models/multilingual/multi-dataset/xtts_v2",
    
    # Voice settings
    "language": "en",  # Options: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko
    "speaker_wav": "reference_audio/d378df9e-566c-41dd-8144-a14229510726-1753356331.wav",  # Path to reference audio for voice cloning (6+ seconds, WAV format)
                    # If None, you must provide one - XTTS requires reference audio
    
    # Quality settings
    "temperature": 0.75,  # 0.1-1.0: Lower = more consistent, Higher = more expressive
    "length_penalty": 1.0,
    "repetition_penalty": 7.0,
    "top_k": 50,
    "top_p": 0.85,
    
    # Processing settings
    "enable_text_splitting": True,  # Split long texts for better quality
    "speed": 1.0,  # Playback speed multiplier
}

# GPU Settings
GPU_CONFIG = {
    "use_gpu": True,  # Set to False to use CPU only
    "gpu_id": 0,  # GPU device ID
}

# PDF Processing Settings
PDF_CONFIG = {
    "sample_paragraphs": 3,  # Number of paragraphs for sample generation
    "chunk_size": 500,  # Characters per TTS chunk (smaller = better quality, slower)
    "remove_page_numbers": True,
    "remove_headers_footers": True,
}

# Audio Export Settings
AUDIO_CONFIG = {
    "format": "mp3",  # Options: mp3, wav, ogg
    "bitrate": "192k",  # For MP3: 128k, 192k, 320k
    "sample_rate": 24000,  # Hz
    "channels": 1,  # Mono
}

# Sample Generation Settings
SAMPLE_CONFIG = {
    "enabled": True,  # Always generate sample first
    "sample_text_length": 1000,  # Characters to use for sample (roughly 1-2 paragraphs)
    "auto_play": False,  # Automatically play sample after generation
}

# Emotion Control Settings (OPTIONAL - Advanced Feature)
EMOTION_CONFIG = {
    "enabled": False,  # Set to True to enable emotion-aware generation
    "config_file": "emotion_config.txt",  # Path to emotion configuration file
    # When enabled:
    # - System detects emotional words/phrases in text
    # - Uses different voice samples for different emotions
    # - Example: "I love you" uses happy voice, "sadly" uses somber voice
    # Run: python emotion_controller.py to generate sample config file
}
