# Character Voice Cloning Guide

SAA uses advanced AI to detect characters in your book and assign them unique voices.

## How It Works
1. **Detection**: The agent analyzes text for dialogue patterns (e.g., "she said", "he shouted").
2. **Assignment**: Characters are mapped to voice profiles based on gender and role.
3. **Cloning**: The TTS engine clones the voice from a reference audio file.

## Setting Up Reference Audio

You need to provide reference audio files in the `reference_audio/` directory.

### Required Files
- `narrator.wav`: The main voice for narration.
- `male.wav`: Default voice for male characters.
- `female.wav`: Default voice for female characters.

### Audio Requirements
- **Format**: WAV
- **Duration**: 6-15 seconds
- **Sample Rate**: 22050 Hz (recommended)
- **Content**: Clear speech, no background noise, no music.

### Tips for Best Results
- Use a high-quality recording.
- Ensure the speaker's voice is consistent throughout the clip.
- Avoid clips with long pauses or extreme emotional variance.

## Advanced Configuration
(Coming in v2.1.0: Custom character-to-voice mapping via config)
