"""
AudioBook TTS - Convert PDF to Audiobook using AI Voice
Main entry point with sample preview feature
"""
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import colorama
from colorama import Fore, Style

from config import (
    TTS_CONFIG, PDF_CONFIG, SAMPLE_CONFIG, 
    OUTPUT_DIR, SAMPLE_DIR, AUDIO_CONFIG
)
from pdf_processor import PDFProcessor
from tts_engine import TTSEngine
from audio_utils import AudioProcessor

# Initialize colorama for Windows
colorama.init()


class AudioBookGenerator:
    """Main AudioBook generation system"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_processor = None
        self.tts_engine = None
        self.audio_processor = None
        
        # Initialize components
        print(f"{Fore.CYAN}{'='*60}")
        print(f"AudioBook TTS System - PDF to Audiobook Converter")
        print(f"{'='*60}{Style.RESET_ALL}\n")
    
    def initialize(self):
        """Initialize all components"""
        print(f"{Fore.YELLOW}[1/3] 📄 Loading Document...{Style.RESET_ALL}")
        
        # Show progress for document loading
        with tqdm(total=3, desc="Loading", bar_format="{desc}", leave=False) as pbar:
            self.pdf_processor = PDFProcessor(self.pdf_path)
            pbar.update(1)
            pdf_info = self.pdf_processor.get_info()
            pbar.update(2)
        
        print(f"  ✓ Document: {pdf_info['filename']}")
        print(f"  ✓ Type: {pdf_info.get('file_type', 'PDF').upper()}")
        print(f"  ✓ Pages: {pdf_info['pages']}")
        print(f"  ✓ Words: {pdf_info['total_words']:,}")
        print(f"  ✓ Estimated duration: {pdf_info['estimated_duration_minutes']:.1f} minutes\n")
        
        print(f"{Fore.YELLOW}[2/3] 🤖 Initializing TTS Engine...{Style.RESET_ALL}")
        self.tts_engine = TTSEngine()
        self.tts_engine.initialize()
        
        tts_info = self.tts_engine.get_info()
        print(f"  ✓ Model: {tts_info['model'].split('/')[-1]}")
        print(f"  ✓ Language: {tts_info['language']}")
        if 'gpu_name' in tts_info:
            print(f"  ✓ GPU: {tts_info['gpu_name']} ({tts_info['vram_total_gb']:.1f} GB)\n")
        
        print(f"{Fore.YELLOW}[3/3] 🎵 Initializing Audio Processor...{Style.RESET_ALL}")
        self.audio_processor = AudioProcessor()
        print()
    
    def generate_sample(self, sample_length: int = None) -> str:
        """
        Generate a sample audio to preview voice and quality
        
        Args:
            sample_length: Characters to use for sample (default from config)
        
        Returns:
            Path to sample audio file
        """
        sample_length = sample_length or SAMPLE_CONFIG['sample_text_length']
        
        print(f"{Fore.GREEN}{'='*60}")
        print(f"SAMPLE GENERATION MODE")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Get sample text
        sample_text = self.pdf_processor.get_sample_text(sample_length)
        
        print(f"Sample text ({len(sample_text)} characters):")
        print(f"{Fore.CYAN}{'-'*60}")
        print(f"{sample_text[:300]}...")
        print(f"{'-'*60}{Style.RESET_ALL}\n")
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample_file = SAMPLE_DIR / f"sample_{timestamp}.wav"
        
        print(f"{Fore.YELLOW}Generating sample audio...{Style.RESET_ALL}")
        
        # Show progress with spinner while generating
        import time
        import threading
        
        generation_complete = threading.Event()
        
        def show_progress():
            """Show elapsed time while generating"""
            start_time = time.time()
            spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            idx = 0
            while not generation_complete.is_set():
                elapsed = int(time.time() - start_time)
                mins, secs = divmod(elapsed, 60)
                print(f"\r{Fore.CYAN}🎙️  {spinner[idx % len(spinner)]} Generating... {mins:02d}:{secs:02d} elapsed{Style.RESET_ALL}", end='', flush=True)
                idx += 1
                time.sleep(0.1)
            # Clear the line
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            print(f"\r{Fore.GREEN}✓ Generated in {mins:02d}:{secs:02d}{Style.RESET_ALL}                    ")
        
        # Start progress thread
        progress_thread = threading.Thread(target=show_progress, daemon=True)
        progress_thread.start()
        
        # Generate sample
        self.tts_engine.generate_speech(
            text=sample_text,
            output_path=str(sample_file)
        )
        
        # Stop progress thread
        generation_complete.set()
        progress_thread.join(timeout=1)
        
        # Convert to final format
        if AUDIO_CONFIG['format'] != 'wav':
            from pydub import AudioSegment
            audio = AudioSegment.from_wav(sample_file)
            final_file = sample_file.with_suffix(f".{AUDIO_CONFIG['format']}")
            
            export_params = {'format': AUDIO_CONFIG['format']}
            if AUDIO_CONFIG['format'] == 'mp3':
                export_params['bitrate'] = AUDIO_CONFIG['bitrate']
            
            audio.export(str(final_file), **export_params)
            sample_file.unlink()  # Remove wav
            sample_file = final_file
        
        # Get audio info
        audio_info = self.audio_processor.get_audio_info(str(sample_file))
        
        print(f"\n{Fore.GREEN}✓ Sample generated successfully!{Style.RESET_ALL}")
        print(f"  → Location: {sample_file}")
        print(f"  → Duration: {audio_info['duration_formatted']}")
        print(f"  → Size: {audio_info['file_size_mb']:.2f} MB\n")
        
        print(f"{Fore.CYAN}{'='*60}")
        print(f"LISTEN TO THE SAMPLE NOW!")
        print(f"{'='*60}{Style.RESET_ALL}")
        print(f"\nPlay the file to check voice quality, speed, and style.")
        print(f"You can adjust settings in config.py:\n")
        print(f"  • temperature: {TTS_CONFIG['temperature']} (0.1-1.0)")
        print(f"  • speed: {TTS_CONFIG['speed']} (0.5-2.0)")
        print(f"  • language: {TTS_CONFIG['language']}")
        print(f"  • bitrate: {AUDIO_CONFIG['bitrate']}\n")
        
        return str(sample_file)
    
    def generate_full_audiobook(self, output_filename: str = None) -> str:
        """
        Generate complete audiobook from PDF
        
        Args:
            output_filename: Custom output filename (optional)
        
        Returns:
            Path to final audiobook file
        """
        print(f"{Fore.GREEN}{'='*60}")
        print(f"FULL AUDIOBOOK GENERATION")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Get text chunks
        print(f"{Fore.YELLOW}Splitting text into chunks...{Style.RESET_ALL}")
        chunks = self.pdf_processor.get_chunks(PDF_CONFIG['chunk_size'])
        print(f"  ✓ Created {len(chunks)} chunks\n")
        
        # Create temp directory for chunks
        temp_dir = OUTPUT_DIR / "temp_chunks"
        temp_dir.mkdir(exist_ok=True)
        
        # Generate audio for each chunk
        print(f"{Fore.YELLOW}Generating audio chunks...{Style.RESET_ALL}")
        print("(This will take a while - grab a coffee! ☕)\n")
        
        generated_files = []
        
        # Enhanced progress bar with ETA and detailed info
        with tqdm(
            total=len(chunks),
            desc=f"{Fore.CYAN}🎙️  Generating Audio{Style.RESET_ALL}",
            unit="chunk",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            colour='cyan',
            ncols=100
        ) as pbar:
            def progress_callback(current, total, text_preview):
                # Update progress bar with chunk preview
                preview = text_preview[:40].replace('\n', ' ')
                pbar.set_postfix_str(f"'{preview}...'")
                pbar.update(1)
            
            generated_files = self.tts_engine.generate_batch(
                texts=chunks,
                output_dir=str(temp_dir),
                base_filename="chunk",
                progress_callback=progress_callback
            )
        
        print(f"\n{Fore.GREEN}✓ Generated {len(generated_files)} audio chunks{Style.RESET_ALL}\n")
        
        # Combine all chunks
        print(f"{Fore.YELLOW}🔗 Combining audio chunks...{Style.RESET_ALL}")
        
        if output_filename is None:
            pdf_name = Path(self.pdf_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{pdf_name}_audiobook_{timestamp}.{AUDIO_CONFIG['format']}"
        
        output_path = OUTPUT_DIR / output_filename
        
        # Show progress for combining
        with tqdm(
            total=len(generated_files),
            desc=f"{Fore.GREEN}🎵 Merging Chunks{Style.RESET_ALL}",
            unit="file",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
            colour='green',
            ncols=100
        ) as combine_pbar:
            # Update progress as files are processed
            combine_pbar.update(0)  # Initialize
            
            final_audio = self.audio_processor.combine_audio_files(
                audio_files=generated_files,
                output_path=str(output_path),
                crossfade_ms=100  # Smooth transitions
            )
            
            combine_pbar.update(len(generated_files))  # Complete
        
        # Get final audio info
        audio_info = self.audio_processor.get_audio_info(final_audio)
        
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"✓ AUDIOBOOK COMPLETE!")
        print(f"{'='*60}{Style.RESET_ALL}")
        print(f"\n  📖 Source: {Path(self.pdf_path).name}")
        print(f"  🎧 Output: {output_path}")
        print(f"  ⏱  Duration: {audio_info['duration_formatted']}")
        print(f"  💾 Size: {audio_info['file_size_mb']:.2f} MB")
        print(f"  🎵 Format: {AUDIO_CONFIG['format'].upper()} @ {AUDIO_CONFIG['bitrate']}\n")
        
        # Cleanup temp files
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
    # Check if file path provided as argument
    if len(sys.argv) < 2:
        # Look for files in input folder
        input_folder = Path("input")
        
        if not input_folder.exists():
            input_folder.mkdir()
        
        # Find PDF or TXT files in input folder
        pdf_files = list(input_folder.glob("*.pdf"))
        txt_files = list(input_folder.glob("*.txt"))
        all_files = pdf_files + txt_files
        
        if not all_files:
            print(f"{Fore.RED}Error: No PDF or TXT files found!{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}Please place your file in one of these locations:{Style.RESET_ALL}")
            print(f"  1. input/ folder (recommended) - supports PDF and TXT")
            print(f"  2. Or run: python audiobook.py <file_path>")
            print(f"\n{Fore.YELLOW}Example:{Style.RESET_ALL}")
            print(f"  python audiobook.py mybook.pdf")
            print(f"  python audiobook.py story.txt")
            sys.exit(1)
        
        if len(all_files) > 1:
            print(f"{Fore.YELLOW}Multiple files found in input/ folder:{Style.RESET_ALL}\n")
            for i, file in enumerate(all_files, 1):
                file_size = file.stat().st_size / 1024
                print(f"  {i}. {file.name} ({file_size:.1f} KB)")
            
            print(f"\n{Fore.CYAN}Select file number (or press Enter for first file):{Style.RESET_ALL}")
            choice = input("> ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(all_files):
                file_path = str(all_files[int(choice) - 1])
            else:
                file_path = str(all_files[0])
                print(f"Using: {all_files[0].name}")
        else:
            file_path = str(all_files[0])
            print(f"{Fore.CYAN}Found file: {all_files[0].name}{Style.RESET_ALL}\n")
    else:
        file_path = sys.argv[1]
    
    # Verify file exists
    if not Path(file_path).exists():
        print(f"{Fore.RED}Error: File not found: {file_path}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Check file type
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in ['.pdf', '.txt']:
        print(f"{Fore.RED}Error: Unsupported file type: {file_ext}{Style.RESET_ALL}")
        print(f"Supported formats: PDF (.pdf), Text (.txt)")
        sys.exit(1)
    
    # Create generator
    generator = AudioBookGenerator(file_path)
    
    try:
        # Initialize
        generator.initialize()
        
        # Always generate sample first
        sample_path = generator.generate_sample()
        
        # Ask user if they want to proceed with full generation
        print(f"{Fore.YELLOW}\nDo you want to generate the full audiobook?{Style.RESET_ALL}")
        print("This will take significant time depending on file length.")
        response = input("Continue? (y/n): ").lower()
        
        if response == 'y':
            generator.generate_full_audiobook()
        else:
            print(f"\n{Fore.CYAN}Sample saved. Adjust config.py and run again when ready!{Style.RESET_ALL}")
    
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
