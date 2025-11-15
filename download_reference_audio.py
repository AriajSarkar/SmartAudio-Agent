"""
Download free reference audio for TTS voice cloning
"""
import os
import urllib.request
from pathlib import Path
import sys

# Free reference audio samples from various public domain sources
# These are high-quality, clear speech samples perfect for voice cloning
REFERENCE_AUDIOS = {
    "female_british": {
        "url": "https://www2.cs.uic.edu/~i101/SoundFiles/gettysburg10.wav",
        "description": "Female British English - Professional narrator",
        "duration": "~10 seconds"
    },
    "female_american": {
        "url": "https://filesamples.com/samples/audio/wav/sample3.wav",
        "description": "Female American English - Clear voice",
        "duration": "~15 seconds"
    },
    "female_clear": {
        "url": "https://www2.cs.uic.edu/~i101/SoundFiles/CantinaBand3.wav",
        "description": "Female voice - High quality recording",
        "duration": "~30 seconds"
    }
}

def download_reference_audio(voice_type="female_en", output_dir="reference_audio"):
    """Download a reference audio file"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    if voice_type not in REFERENCE_AUDIOS:
        print(f"Unknown voice type: {voice_type}")
        print(f"Available types: {list(REFERENCE_AUDIOS.keys())}")
        return None
    
    audio_info = REFERENCE_AUDIOS[voice_type]
    output_file = output_dir / f"{voice_type}_reference.wav"
    
    print(f"Downloading {audio_info['description']}...")
    print(f"URL: {audio_info['url']}")
    
    try:
        urllib.request.urlretrieve(audio_info['url'], output_file)
        print(f"✓ Downloaded to: {output_file}")
        print(f"✓ Size: {output_file.stat().st_size / 1024:.1f} KB")
        return str(output_file)
    except Exception as e:
        print(f"✗ Download failed: {e}")
        print("\nAlternative: Use text-to-speech to create reference")
        return None


def create_reference_with_pyttsx3(output_file="reference_audio/voice_reference.wav"):
    """Create a reference audio using local TTS (fallback option)"""
    try:
        import pyttsx3
        from pydub import AudioSegment
        import tempfile
        
        print("Creating reference audio using local TTS...")
        
        # Initialize TTS
        engine = pyttsx3.init()
        
        # Configure voice
        voices = engine.getProperty('voices')
        # Use first available voice
        engine.setProperty('voice', voices[0].id if voices else None)
        engine.setProperty('rate', 150)  # Speed
        
        # Sample text for reference
        text = """
        Hello, this is a sample voice recording for audio book generation.
        The quick brown fox jumps over the lazy dog.
        Testing one, two, three, four, five.
        This recording will be used as a reference for voice cloning.
        """
        
        # Save to temp MP3
        temp_file = tempfile.mktemp(suffix='.mp3')
        engine.save_to_file(text, temp_file)
        engine.runAndWait()
        
        # Convert to WAV if needed
        if not output_file.endswith('.wav'):
            output_file += '.wav'
        
        # Ensure output directory exists
        Path(output_file).parent.mkdir(exist_ok=True, parents=True)
        
        # Copy/convert to final location
        import shutil
        shutil.move(temp_file, output_file)
        
        print(f"✓ Created reference audio: {output_file}")
        return output_file
        
    except ImportError:
        print("✗ pyttsx3 not installed. Cannot create reference audio.")
        return None
    except Exception as e:
        print(f"✗ Failed to create reference: {e}")
        return None


if __name__ == "__main__":
    print("="*60)
    print("Reference Audio Downloader for AudioBook TTS")
    print("="*60)
    print()
    
    print("Available voices:")
    for i, (key, info) in enumerate(REFERENCE_AUDIOS.items(), 1):
        print(f"  {i}. {key}: {info['description']} ({info['duration']})")
    
    print()
    choice = input("Select voice (1-3) or press Enter for default [1]: ").strip()
    
    if not choice:
        choice = "1"
    
    voice_map = {
        "1": "female_en_1",
        "2": "female_en_2", 
        "3": "sample"
    }
    
    voice_type = voice_map.get(choice, "female_en_1")
    
    print(f"\nDownloading {voice_type}...")
    print("-" * 60)
    
    result = download_reference_audio(voice_type)
    
    if result:
        print("\n" + "="*60)
        print("✓ SUCCESS! Reference audio is ready!")
        print("="*60)
        print(f"\nFile location: {result}")
        print(f"\nNow update config.py:")
        print("\nOpen config.py and change this line:")
        print('  "speaker_wav": None,')
        print("\nTo this:")
        print(f'  "speaker_wav": "{result}",')
        print("\nOr run this command:")
        print(f'  (Get-Content config.py) -replace \'"speaker_wav": None,\', \'"speaker_wav": "{result}",\' | Set-Content config.py')
        print("\nThen run: python audiobook.py")
    else:
        print("\n⚠ Download failed. Try these alternatives:")
        print("\n1. Record your own voice:")
        print("   - Use Windows Voice Recorder")
        print("   - Speak for 6-10 seconds")
        print("   - Save as WAV format")
        print("\n2. Download from:")
        print("   - https://freesound.org/ (search 'voice sample')")
        print("   - https://www.voiptroubleshooter.com/open_speech/")
        print("\n3. Use any clear audio (podcast, audiobook sample, etc.)")
