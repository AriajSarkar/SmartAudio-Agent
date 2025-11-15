"""
TTS.pdf Audiobook Generator with Character Voices
Specialized script for generating audiobook with different voices per character
"""
import sys
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_processor import DocumentProcessor
from tts_engine import TTSEngine
from audio_utils import AudioProcessor
from character_voice_manager import create_tts_pdf_config
from config import PDF_CONFIG, AUDIO_CONFIG, OUTPUT_DIR, SAMPLE_DIR

init(autoreset=True)


class CharacterAudiobookGenerator:
    """Generate audiobook with character-specific voices"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_processor = None
        self.tts_engine = None
        self.audio_processor = None
        self.character_manager = None
        
        print(f"{Fore.CYAN}{'='*60}")
        print(f"Character-Based Audiobook Generator for TTS.pdf")
        print(f"{'='*60}{Style.RESET_ALL}\n")
    
    def initialize(self):
        """Initialize all components"""
        print(f"{Fore.YELLOW}[1/4] 📄 Loading PDF and filtering text...{Style.RESET_ALL}")
        
        # Load PDF
        self.pdf_processor = DocumentProcessor(self.pdf_path)
        self.pdf_processor.extract_text()
        
        # Apply text filtering
        self.character_manager = create_tts_pdf_config()
        self.pdf_processor.text = self.character_manager.filter_text(self.pdf_processor.text)
        
        # Re-chunk after filtering
        words = self.pdf_processor.text.split()
        self.pdf_processor.pages = []
        page_size = 500
        for i in range(0, len(words), page_size):
            page_text = ' '.join(words[i:i + page_size])
            self.pdf_processor.pages.append({
                'number': (i // page_size) + 1,
                'text': page_text
            })
        
        pdf_info = self.pdf_processor.get_info()
        print(f"  ✓ Document: {pdf_info['filename']}")
        print(f"  ✓ Filtered pages: {pdf_info['pages']}")
        print(f"  ✓ Words: {pdf_info['total_words']:,}")
        print(f"  ✓ Copyright/acknowledgments removed\n")
        
        print(f"{Fore.YELLOW}[2/4] 🎭 Setting up character voices...{Style.RESET_ALL}")
        print(f"  ✓ Sadie Wen → female.wav")
        print(f"  ✓ Julius Gong → male.wav")
        print(f"  ✓ Abigail Ong → female.wav")
        print(f"  ✓ Ray Suzuki → male.wav")
        print(f"  ✓ Narrator → dynamic (male/female based on context)\n")
        
        print(f"{Fore.YELLOW}[3/4] 🤖 Initializing TTS Engine...{Style.RESET_ALL}")
        self.tts_engine = TTSEngine()
        self.tts_engine.initialize()
        print(f"  ✓ Engine ready for voice switching\n")
        
        print(f"{Fore.YELLOW}[4/4] 🎵 Initializing Audio Processor...{Style.RESET_ALL}")
        self.audio_processor = AudioProcessor()
        print(f"  ✓ Ready to process\n")
    
    def generate_sample(self, sample_length: int = 1000):
        """Generate sample with character voice"""
        print(f"{Fore.GREEN}{'='*60}")
        print(f"SAMPLE GENERATION WITH CHARACTER VOICES")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Get sample text
        sample_text = self.pdf_processor.get_sample_text(sample_length)
        
        # Detect voice for sample
        character, voice_file = self.character_manager.detect_speaker(sample_text)
        
        print(f"Detected speaker: {Fore.CYAN}{character}{Style.RESET_ALL}")
        print(f"Using voice: {Fore.CYAN}{voice_file}{Style.RESET_ALL}\n")
        
        print(f"Sample text preview:")
        print(f"{Fore.CYAN}{'-'*60}")
        print(f"{sample_text[:200]}...")
        print(f"{'-'*60}{Style.RESET_ALL}\n")
        
        # Generate audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample_file = SAMPLE_DIR / f"sample_character_{timestamp}.wav"
        
        print(f"{Fore.YELLOW}Generating sample audio...{Style.RESET_ALL}\n")
        
        import time
        import threading
        
        generation_complete = threading.Event()
        
        def show_progress():
            start_time = time.time()
            spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            idx = 0
            while not generation_complete.is_set():
                elapsed = int(time.time() - start_time)
                mins, secs = divmod(elapsed, 60)
                print(f"\r{Fore.CYAN}🎙️  {spinner[idx % len(spinner)]} Generating with {character}'s voice... {mins:02d}:{secs:02d}{Style.RESET_ALL}", end='', flush=True)
                idx += 1
                time.sleep(0.1)
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            print(f"\r{Fore.GREEN}✓ Generated in {mins:02d}:{secs:02d}{Style.RESET_ALL}" + " " * 30)
        
        progress_thread = threading.Thread(target=show_progress, daemon=True)
        progress_thread.start()
        
        self.tts_engine.generate_speech(
            text=sample_text,
            output_path=str(sample_file),
            speaker_wav=voice_file
        )
        
        generation_complete.set()
        progress_thread.join(timeout=1)
        
        # Convert to final format (keep as WAV for now - simpler and works)
        # WAV format is lossless and works perfectly for audiobooks
        print(f"\n{Fore.GREEN}✓ Sample generated successfully!{Style.RESET_ALL}")
        print(f"  → Location: {sample_file}")
        print(f"  → Format: WAV (lossless)")
        print(f"  → Character voice: {character}\n")
        
        return str(sample_file)
    
    def generate_full_audiobook(self):
        """Generate full audiobook with character voices"""
        print(f"{Fore.GREEN}{'='*60}")
        print(f"FULL AUDIOBOOK WITH CHARACTER VOICES")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Get text
        print(f"{Fore.YELLOW}Splitting text by speaker changes...{Style.RESET_ALL}")
        
        # Use smart speaker-based chunking
        # Text was already extracted during initialization
        full_text = self.pdf_processor.text
        chunks = self.character_manager.smart_split_by_speaker(
            full_text, 
            max_chunk_size=PDF_CONFIG['chunk_size']
        )
        print(f"  ✓ Created {len(chunks)} speaker-based chunks\n")
        
        # Assign voices to chunks
        print(f"{Fore.YELLOW}Analyzing chunks and assigning character voices...{Style.RESET_ALL}")
        processed_chunks = self.character_manager.process_chunks_with_voices(chunks)
        
        # Show voice distribution
        voice_summary = self.character_manager.get_voice_summary(processed_chunks)
        print(f"\n{Fore.CYAN}Voice Distribution:{Style.RESET_ALL}")
        for character, count in voice_summary.items():
            percentage = (count / len(chunks)) * 100
            print(f"  • {character}: {count} chunks ({percentage:.1f}%)")
        print()
        
        # Create temp directory
        temp_dir = OUTPUT_DIR / "temp_chunks"
        temp_dir.mkdir(exist_ok=True)
        
        # Generate audio for each chunk with appropriate voice
        print(f"{Fore.YELLOW}Generating audio with character voices...{Style.RESET_ALL}")
        print("(This will take a while - grab a coffee! ☕)\n")
        
        generated_files = []
        
        with tqdm(
            total=len(processed_chunks),
            desc=f"{Fore.CYAN}🎭 Generating with Character Voices{Style.RESET_ALL}",
            unit="chunk",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            colour='cyan',
            ncols=100
        ) as pbar:
            for chunk_data in processed_chunks:
                idx = chunk_data['chunk_index']
                text = chunk_data['text']
                voice_file = chunk_data['voice_file']
                character = chunk_data['character']
                
                output_path = temp_dir / f"chunk_{idx:04d}.wav"
                
                # Update progress with character info
                char_short = character.split()[0]  # First name only
                preview = text[:30].replace('\n', ' ')
                pbar.set_postfix_str(f"{char_short}: '{preview}...'")
                
                try:
                    self.tts_engine.generate_speech(
                        text=text,
                        output_path=str(output_path),
                        speaker_wav=voice_file
                    )
                    generated_files.append(str(output_path))
                except Exception as e:
                    print(f"\n✗ Error on chunk {idx}: {e}")
                    continue
                
                pbar.update(1)
        
        print(f"\n{Fore.GREEN}✓ Generated {len(generated_files)} audio chunks{Style.RESET_ALL}\n")
        
        # Combine chunks
        print(f"{Fore.YELLOW}🔗 Combining audio chunks...{Style.RESET_ALL}\n")
        
        pdf_name = Path(self.pdf_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{pdf_name}_character_voices_{timestamp}.{AUDIO_CONFIG['format']}"
        output_path = OUTPUT_DIR / output_filename
        
        with tqdm(
            total=len(generated_files),
            desc=f"{Fore.GREEN}🎵 Merging{Style.RESET_ALL}",
            unit="file",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
            colour='green',
            ncols=100
        ) as pbar:
            pbar.update(0)
            final_audio = self.audio_processor.combine_audio_files(
                audio_files=generated_files,
                output_path=str(output_path),
                crossfade_ms=100
            )
            pbar.update(len(generated_files))
        
        audio_info = self.audio_processor.get_audio_info(final_audio)
        
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"✓ CHARACTER AUDIOBOOK COMPLETE!")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        print(f"  📖 Source: {Path(self.pdf_path).name}")
        print(f"  🎭 Multiple character voices used")
        print(f"  🎧 Output: {output_path}")
        print(f"  ⏱  Duration: {audio_info['duration_formatted']}")
        print(f"  💾 Size: {audio_info['file_size_mb']:.2f} MB\n")
        
        # Cleanup
        if input(f"Delete temporary chunk files? (y/n): ").lower() == 'y':
            self.audio_processor.cleanup_temp_files(generated_files)
            temp_dir.rmdir()
        
        return str(output_path)
    
    def cleanup(self):
        """Cleanup resources"""
        if self.tts_engine:
            self.tts_engine.cleanup()


def main():
    """Main entry point"""
    # Check for test file first, then TTS.pdf
    test_file = Path("input/test-character-voices.txt")
    pdf_file = Path("input/TTS.pdf")
    
    if test_file.exists():
        file_path = str(test_file)
        print(f"{Fore.CYAN}Found test file: test-character-voices.txt{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Testing character voice system...{Style.RESET_ALL}\n")
    elif pdf_file.exists():
        file_path = str(pdf_file)
        print(f"{Fore.CYAN}Found: TTS.pdf{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Processing full book with character voices...{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}Error: No input file found!{Style.RESET_ALL}")
        print(f"\nPlease place one of these files in input/ folder:")
        print(f"  - test-character-voices.txt (for quick testing)")
        print(f"  - TTS.pdf (for full audiobook)")
        sys.exit(1)
    
    # Check voice files
    female_voice = Path("reference_audio/female.wav")
    male_voice = Path("reference_audio/male.wav")
    
    if not female_voice.exists() or not male_voice.exists():
        print(f"{Fore.RED}Error: Voice files not found!{Style.RESET_ALL}")
        print(f"Please ensure these files exist:")
        print(f"  - reference_audio/female.wav")
        print(f"  - reference_audio/male.wav")
        sys.exit(1)
    
    generator = CharacterAudiobookGenerator(file_path)
    
    try:
        generator.initialize()
        generator.generate_sample()
        
        print(f"\n{Fore.YELLOW}Do you want to generate the full audiobook with character voices?{Style.RESET_ALL}")
        response = input("Continue? (y/n): ").lower()
        
        if response == 'y':
            generator.generate_full_audiobook()
        else:
            print(f"\n{Fore.CYAN}Sample saved. Run again when ready!{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
    finally:
        generator.cleanup()


if __name__ == "__main__":
    main()
