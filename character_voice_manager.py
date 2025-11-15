"""
Character Voice Manager for TTS.pdf
Handles character detection and voice switching for specific books
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class CharacterVoiceManager:
    """Manages character-based voice switching for audiobooks"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize with character configuration
        
        Args:
            config_file: Path to character config file (optional)
        """
        self.characters = {}
        self.voice_mappings = {}
        self.text_filters = []
        
        if config_file and Path(config_file).exists():
            self.load_config(config_file)
    
    def add_character(self, name: str, gender: str, voice_file: str, keywords: List[str] = None):
        """
        Add a character with voice mapping
        
        Args:
            name: Character name
            gender: 'male' or 'female'
            voice_file: Path to reference audio file
            keywords: Additional keywords to detect this character
        """
        self.characters[name] = {
            'gender': gender,
            'voice_file': voice_file,
            'keywords': keywords or []
        }
        self.voice_mappings[name.lower()] = voice_file
    
    def add_text_filter(self, pattern: str, filter_type: str = 'remove'):
        """
        Add text filter to remove unwanted content
        
        Args:
            pattern: Regex pattern or exact text to filter
            filter_type: 'remove' or 'replace'
        """
        self.text_filters.append({
            'pattern': pattern,
            'type': filter_type
        })
    
    def filter_text(self, text: str) -> str:
        """
        Remove unwanted text like copyright notices
        
        Args:
            text: Original text
            
        Returns:
            Filtered text
        """
        filtered = text
        
        # Remove copyright block
        copyright_pattern = r'Copyright © \d{4}.*?(?=\n\n[A-Z]|\Z)'
        filtered = re.sub(copyright_pattern, '', filtered, flags=re.DOTALL | re.MULTILINE)
        
        # Remove acknowledgments section and everything after
        ack_pattern = r'A C K N O W L E D G M E N T S.*'
        filtered = re.sub(ack_pattern, '', filtered, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove page markers
        filtered = re.sub(r'INT_\d+\.indd.*?\d{1,2}/\d{1,2}/\d{2,4}.*?[AP]M', '', filtered)
        
        # Remove "FOR MY READERS" section
        filtered = re.sub(r'FOR MY READERS.*?\n', '', filtered, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        filtered = re.sub(r'\n{3,}', '\n\n', filtered)
        filtered = filtered.strip()
        
        return filtered
    
    def detect_speaker(self, text: str, context: str = "") -> Tuple[str, str]:
        """
        Advanced speaker detection using multiple strategies
        
        Args:
            text: Text to analyze
            context: Surrounding context for better detection
            
        Returns:
            Tuple of (character_name, voice_file)
        """
        text_lower = text.lower()
        
        # STRATEGY 1: Dialogue attribution patterns (MOST RELIABLE)
        # Look for patterns like: "said Ray", "Julius replied", "Sadie asked"
        dialogue_patterns = [
            r'said\s+(\w+)',
            r'(\w+)\s+said',
            r'replied\s+(\w+)',
            r'(\w+)\s+replied',
            r'asked\s+(\w+)',
            r'(\w+)\s+asked',
            r'exclaimed\s+(\w+)',
            r'(\w+)\s+exclaimed',
            r'shouted\s+(\w+)',
            r'(\w+)\s+shouted',
            r'whispered\s+(\w+)',
            r'(\w+)\s+whispered',
            r'muttered\s+(\w+)',
            r'(\w+)\s+muttered',
        ]
        
        for pattern in dialogue_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                potential_name = match.group(1)
                # Check if this matches any character's first name
                for name, info in self.characters.items():
                    first_name = name.split()[0].lower()
                    if potential_name == first_name:
                        return name, info['voice_file']
        
        # STRATEGY 2: Paragraph starts with character name
        text_start = text[:100].lower()
        for name, info in self.characters.items():
            first_name = name.split()[0].lower()
            if text_start.startswith(first_name) or text_start.startswith(f"{first_name} "):
                return name, info['voice_file']
        
        # STRATEGY 3: Character name in first sentence
        first_sentence = text.split('.')[0].lower() if '.' in text else text_lower[:200]
        for name, info in self.characters.items():
            first_name = name.split()[0].lower()
            # Only count if name appears at start of first sentence
            if first_sentence.startswith(first_name) or f" {first_name} " in first_sentence[:50]:
                return name, info['voice_file']
        
        # STRATEGY 4: Pronoun tracking with gender mapping
        # Build character scores based on pronouns and context
        scores = {}
        
        feminine_pronouns = ['she', 'her', 'herself']
        masculine_pronouns = ['he', 'him', 'himself']
        
        fem_count = sum(text_lower.split().count(p) for p in feminine_pronouns)
        masc_count = sum(text_lower.split().count(p) for p in masculine_pronouns)
        
        # Assign scores to characters based on gender
        for name, info in self.characters.items():
            score = 0
            if info['gender'] == 'female' and fem_count > 0:
                score = fem_count
            elif info['gender'] == 'male' and masc_count > 0:
                score = masc_count
            
            # Boost score if character keywords appear
            for keyword in info['keywords']:
                if keyword.lower() in text_lower:
                    score += 5
            
            scores[name] = score
        
        # Return character with highest score if clear winner
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                for name, score in scores.items():
                    if score == max_score:
                        return name, self.characters[name]['voice_file']
        
        # FALLBACK: Narrator voice based on pronoun dominance
        if fem_count > masc_count:
            return "Narrator (Female)", "reference_audio/female.wav"
        elif masc_count > fem_count:
            return "Narrator (Male)", "reference_audio/male.wav"
        else:
            return "Narrator (Female)", "reference_audio/female.wav"
    
    def smart_split_by_speaker(self, text: str, max_chunk_size: int = 250) -> List[str]:
        """
        Split text into chunks based on speaker changes and dialogue
        Also ensures chunks don't exceed TTS character limit (250 chars recommended)
        
        Args:
            text: Full text to split
            max_chunk_size: Maximum words per chunk (default 250)
            
        Returns:
            List of text chunks split at speaker boundaries
        """
        # Split into paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_words = 0
        current_speaker = None
        
        # TTS model has ~250 CHARACTER limit per segment (not words!)
        # We'll aim for max 200 chars to be safe
        MAX_CHARS_PER_CHUNK = 800  # Safe limit for TTS processing
        
        for i, para in enumerate(paragraphs):
            para_words = len(para.split())
            para_chars = len(para)
            
            # Detect if this paragraph STARTS with a character name
            # This is more reliable than checking if name appears anywhere
            detected_speaker = None
            para_start = para[:50].lower()  # Check first 50 chars only
            
            for name in self.characters.keys():
                first_name = name.split()[0].lower()
                # Check if paragraph starts with character name
                if para_start.startswith(first_name) or f" {first_name} " in para_start[:30]:
                    detected_speaker = name
                    break
            
            # Always split when we detect a new speaker starting a paragraph
            should_split = False
            
            if detected_speaker:
                # New speaker detected - always split (unless it's the first chunk)
                if current_chunk and detected_speaker != current_speaker:
                    should_split = True
                current_speaker = detected_speaker
            
            # Get current chunk character count
            current_chunk_chars = len('\n\n'.join(current_chunk))
            
            # Split if chunk would exceed character limit
            if (current_chunk_chars + para_chars > MAX_CHARS_PER_CHUNK and current_chunk) or \
               (current_words + para_words > max_chunk_size and current_chunk):
                should_split = True
            
            # Perform the split
            if should_split:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_words = para_words
            else:
                current_chunk.append(para)
                current_words += para_words
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        # POST-PROCESSING: Split any chunks that are still too long
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= MAX_CHARS_PER_CHUNK:
                final_chunks.append(chunk)
            else:
                # Split by sentences
                sentences = chunk.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|')
                sub_chunk = []
                sub_chunk_chars = 0
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    sentence_chars = len(sentence)
                    
                    if sub_chunk_chars + sentence_chars > MAX_CHARS_PER_CHUNK and sub_chunk:
                        # Save current sub-chunk
                        final_chunks.append(' '.join(sub_chunk))
                        sub_chunk = [sentence]
                        sub_chunk_chars = sentence_chars
                    else:
                        sub_chunk.append(sentence)
                        sub_chunk_chars += sentence_chars
                
                # Add remaining sentences
                if sub_chunk:
                    final_chunks.append(' '.join(sub_chunk))
        
        return final_chunks
    
    def process_chunks_with_voices(self, chunks: List[str]) -> List[Dict[str, str]]:
        """
        Process text chunks and assign appropriate voices
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of dicts with 'text', 'character', 'voice_file'
        """
        processed = []
        context = ""
        
        for i, chunk in enumerate(chunks):
            # Get context from previous chunks
            if i > 0:
                context = chunks[i-1][-200:]  # Last 200 chars of previous chunk
            
            character, voice_file = self.detect_speaker(chunk, context)
            
            processed.append({
                'text': chunk,
                'character': character,
                'voice_file': voice_file,
                'chunk_index': i
            })
        
        return processed
    
    def get_voice_summary(self, processed_chunks: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Get summary of voice usage
        
        Args:
            processed_chunks: Processed chunks with voice assignments
            
        Returns:
            Dictionary of character -> chunk count
        """
        summary = {}
        for chunk in processed_chunks:
            char = chunk['character']
            summary[char] = summary.get(char, 0) + 1
        return summary
    
    def save_config(self, filepath: str):
        """Save character configuration to file"""
        import json
        config = {
            'characters': self.characters,
            'text_filters': self.text_filters
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def load_config(self, filepath: str):
        """Load character configuration from file"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.characters = config.get('characters', {})
            self.text_filters = config.get('text_filters', [])
            
            # Rebuild voice mappings
            for name, info in self.characters.items():
                self.voice_mappings[name.lower()] = info['voice_file']


def create_tts_pdf_config() -> CharacterVoiceManager:
    """
    Create character configuration for TTS.pdf
    
    Returns:
        Configured CharacterVoiceManager
    """
    manager = CharacterVoiceManager()
    
    # Add main characters
    manager.add_character(
        name="Sadie Wen",
        gender="female",
        voice_file="reference_audio/female.wav",
        keywords=["sadie", "she said", "i said", "my"]
    )
    
    manager.add_character(
        name="Julius Gong",
        gender="male",
        voice_file="reference_audio/male.wav",
        keywords=["julius", "he said", "gong"]
    )
    
    manager.add_character(
        name="Abigail Ong",
        gender="female",
        voice_file="reference_audio/female.wav",
        keywords=["abigail", "abi"]
    )
    
    manager.add_character(
        name="Ray Suzuki",
        gender="male",
        voice_file="reference_audio/male.wav",
        keywords=["ray", "suzuki"]
    )
    
    return manager


# Example usage
if __name__ == "__main__":
    # Create config for TTS.pdf
    manager = create_tts_pdf_config()
    
    # Test text filtering
    test_text = """
    Copyright © 2025 by Ann Liang
    All rights reserved. Published by Scholastic Press...
    
    Chapter 1
    
    Sadie walked into the classroom.
    """
    
    filtered = manager.filter_text(test_text)
    print("Filtered text:")
    print(filtered)
    
    # Test speaker detection
    test_chunks = [
        "Sadie walked into the classroom, feeling nervous.",
        "Julius smirked from his seat. 'Ready to lose?' he said.",
        "She ignored him and took her seat.",
    ]
    
    processed = manager.process_chunks_with_voices(test_chunks)
    
    print("\n\nVoice assignments:")
    for chunk in processed:
        print(f"\n{chunk['character']}: {chunk['voice_file']}")
        print(f"Text: {chunk['text'][:50]}...")
    
    # Voice usage summary
    summary = manager.get_voice_summary(processed)
    print("\n\nVoice usage summary:")
    for char, count in summary.items():
        print(f"{char}: {count} chunks")
