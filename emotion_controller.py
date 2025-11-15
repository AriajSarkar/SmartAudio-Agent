"""
Emotion and Emphasis Control for AudioBook TTS
Optional feature - add emotional context to specific words/phrases
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple


class EmotionController:
    """
    Add emotional markers to text for more expressive TTS
    Uses special tags and reference audio samples for different emotions
    """
    
    def __init__(self, emotion_config_file: str = None):
        self.emotions = {}
        self.emphasis_words = {}
        
        if emotion_config_file and Path(emotion_config_file).exists():
            self.load_emotion_config(emotion_config_file)
    
    def load_emotion_config(self, config_file: str):
        """
        Load emotion configuration from text file
        
        Format:
        [EMOTION:happy]
        reference_audio = path/to/happy_voice.wav
        words = excited, wonderful, amazing, love
        
        [EMOTION:sad]
        reference_audio = path/to/sad_voice.wav
        words = unfortunately, sadly, tragic
        
        [EMPHASIS]
        strong = URGENT, IMPORTANT, CRITICAL
        moderate = very, really, extremely
        """
        current_emotion = None
        
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                # Emotion section header
                if line.startswith('[EMOTION:'):
                    emotion_name = line[9:-1]  # Extract emotion name
                    current_emotion = emotion_name
                    self.emotions[emotion_name] = {
                        'reference_audio': None,
                        'words': []
                    }
                
                elif line.startswith('[EMPHASIS]'):
                    current_emotion = 'EMPHASIS'
                
                # Parse key-value pairs
                elif '=' in line and current_emotion:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if current_emotion == 'EMPHASIS':
                        # Parse emphasis levels
                        words = [w.strip() for w in value.split(',')]
                        self.emphasis_words[key] = words
                    
                    elif current_emotion in self.emotions:
                        if key == 'reference_audio':
                            self.emotions[current_emotion]['reference_audio'] = value
                        elif key == 'words':
                            words = [w.strip() for w in value.split(',')]
                            self.emotions[current_emotion]['words'].extend(words)
    
    def detect_emotion_context(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Detect emotional context in text and return chunks with emotions
        
        Returns:
            List of (text_chunk, emotion, reference_audio) tuples
        """
        if not self.emotions:
            # No emotion config, return original text
            return [(text, 'neutral', None)]
        
        chunks = []
        sentences = re.split(r'([.!?]+)', text)
        
        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i]
            punctuation = sentences[i+1] if i+1 < len(sentences) else ''
            full_sentence = sentence + punctuation
            
            # Detect emotion based on keywords
            detected_emotion = 'neutral'
            reference_audio = None
            
            for emotion_name, emotion_data in self.emotions.items():
                emotion_words = emotion_data['words']
                
                # Check if any emotion words are in the sentence
                for word in emotion_words:
                    if re.search(r'\b' + re.escape(word) + r'\b', sentence, re.IGNORECASE):
                        detected_emotion = emotion_name
                        reference_audio = emotion_data['reference_audio']
                        break
                
                if detected_emotion != 'neutral':
                    break
            
            chunks.append((full_sentence.strip(), detected_emotion, reference_audio))
        
        return chunks
    
    def add_emphasis_markers(self, text: str) -> str:
        """
        Add SSML-style emphasis to words based on emphasis configuration
        Note: XTTS doesn't use SSML, but we can use capitalization and punctuation
        """
        if not self.emphasis_words:
            return text
        
        modified_text = text
        
        # Add emphasis through punctuation and spacing
        for level, words in self.emphasis_words.items():
            for word in words:
                if level == 'strong':
                    # Strong emphasis: ALL CAPS with extra punctuation
                    pattern = r'\b(' + re.escape(word) + r')\b'
                    modified_text = re.sub(
                        pattern, 
                        r'**\1**',  # Add markers for strong emphasis
                        modified_text, 
                        flags=re.IGNORECASE
                    )
                elif level == 'moderate':
                    # Moderate emphasis: Keep as is but mark it
                    pattern = r'\b(' + re.escape(word) + r')\b'
                    modified_text = re.sub(
                        pattern,
                        r'*\1*',  # Add markers for moderate emphasis
                        modified_text,
                        flags=re.IGNORECASE
                    )
        
        return modified_text
    
    def process_text_with_emotions(self, text: str) -> List[Dict]:
        """
        Process text and return chunks with emotion metadata
        
        Returns:
            List of dicts with 'text', 'emotion', 'reference_audio'
        """
        # First add emphasis markers
        emphasized_text = self.add_emphasis_markers(text)
        
        # Then detect emotions
        emotion_chunks = self.detect_emotion_context(emphasized_text)
        
        result = []
        for chunk_text, emotion, ref_audio in emotion_chunks:
            result.append({
                'text': chunk_text,
                'emotion': emotion,
                'reference_audio': ref_audio
            })
        
        return result
    
    def create_sample_config(self, output_file: str = "emotion_config.txt"):
        """Create a sample emotion configuration file"""
        sample_config = """# Emotion Configuration for AudioBook TTS
# Define emotions and their associated words/phrases
# Each emotion can have a different reference audio for voice cloning

# Happy/Excited emotion
[EMOTION:happy]
reference_audio = reference_audio/happy_voice.wav
words = excited, wonderful, amazing, love, joy, delighted, thrilled, fantastic

# Sad/Somber emotion
[EMOTION:sad]
reference_audio = reference_audio/sad_voice.wav
words = unfortunately, sadly, tragic, sorrow, grief, disappointed, heartbroken

# Angry/Intense emotion
[EMOTION:angry]
reference_audio = reference_audio/angry_voice.wav
words = furious, outraged, angry, enraged, infuriated, livid

# Calm/Peaceful emotion
[EMOTION:calm]
reference_audio = reference_audio/calm_voice.wav
words = peaceful, serene, tranquil, gentle, soothing, quiet

# Emphasis levels for important words
[EMPHASIS]
strong = URGENT, IMPORTANT, CRITICAL, WARNING, DANGER, ATTENTION
moderate = very, really, extremely, absolutely, definitely, certainly

# Notes:
# - Words are case-insensitive
# - Reference audio should be 6+ seconds of clear speech in that emotional tone
# - If reference_audio file doesn't exist, default voice will be used
# - Emphasis markers (**strong** and *moderate*) add natural pauses
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sample_config)
        
        print(f"✓ Sample emotion config created: {output_file}")
        print("  Edit this file to customize emotions and reference audio")
        return output_file


# Standalone usage
if __name__ == "__main__":
    print("="*60)
    print("Emotion Controller - Sample Configuration Generator")
    print("="*60)
    print()
    
    controller = EmotionController()
    config_file = controller.create_sample_config()
    
    print()
    print("Next steps:")
    print(f"1. Edit {config_file} to add your emotion reference audio files")
    print("2. Record or download different emotional voice samples")
    print("3. The system will automatically use appropriate emotions")
    print()
    print("Example: When text contains 'I love you', it will use the happy voice!")
