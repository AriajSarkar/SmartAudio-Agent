"""
Audio Processing and Export Utilities
"""
import subprocess
from pathlib import Path
from typing import List, Optional
from pydub import AudioSegment
from pydub.utils import which
from config import AUDIO_CONFIG
import os


class AudioProcessor:
    """Handle audio file operations and export"""
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        if self.ffmpeg_path:
            AudioSegment.converter = self.ffmpeg_path
            print(f"✓ FFmpeg found: {self.ffmpeg_path}")
        else:
            print("⚠ FFmpeg not found. Install for better audio quality.")
            print("  Download from: https://ffmpeg.org/download.html")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Locate FFmpeg executable"""
        # Check if ffmpeg is in PATH
        ffmpeg = which("ffmpeg")
        if ffmpeg:
            return ffmpeg
        
        # Check common Windows locations
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            Path.home() / "ffmpeg" / "bin" / "ffmpeg.exe",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return str(path)
        
        return None
    
    def combine_audio_files(
        self,
        audio_files: List[str],
        output_path: str,
        crossfade_ms: int = 0
    ) -> str:
        """
        Combine multiple audio files into one
        
        Args:
            audio_files: List of audio file paths
            output_path: Output file path
            crossfade_ms: Milliseconds of crossfade between chunks
        
        Returns:
            Path to combined audio file
        """
        if not audio_files:
            raise ValueError("No audio files to combine")
        
        print(f"Combining {len(audio_files)} audio chunks...")
        
        # Load first audio file
        combined = AudioSegment.from_wav(audio_files[0])
        
        # Combine remaining files
        for i, audio_file in enumerate(audio_files[1:], 1):
            if i % 10 == 0:
                print(f"  Processing chunk {i}/{len(audio_files)}...")
            
            next_segment = AudioSegment.from_wav(audio_file)
            
            if crossfade_ms > 0:
                combined = combined.append(next_segment, crossfade=crossfade_ms)
            else:
                combined = combined + next_segment
        
        # Export combined audio
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._export_audio(combined, output_path)
        
        print(f"✓ Combined audio saved: {output_path}")
        return str(output_path)
    
    def _export_audio(self, audio: AudioSegment, output_path: Path):
        """Export audio with configured settings"""
        format_ext = AUDIO_CONFIG['format']
        
        export_params = {
            'format': format_ext,
        }
        
        if format_ext == 'mp3':
            export_params['bitrate'] = AUDIO_CONFIG['bitrate']
            export_params['parameters'] = ["-q:a", "2"]  # High quality VBR
        elif format_ext == 'wav':
            export_params['parameters'] = [
                "-ar", str(AUDIO_CONFIG['sample_rate']),
                "-ac", str(AUDIO_CONFIG['channels'])
            ]
        
        # Ensure output has correct extension
        if not str(output_path).endswith(f'.{format_ext}'):
            output_path = output_path.with_suffix(f'.{format_ext}')
        
        audio.export(str(output_path), **export_params)
        
        return output_path
    
    def get_audio_info(self, audio_path: str) -> dict:
        """Get audio file information"""
        audio = AudioSegment.from_file(audio_path)
        
        duration_seconds = len(audio) / 1000
        
        return {
            'duration_seconds': duration_seconds,
            'duration_formatted': self._format_duration(duration_seconds),
            'channels': audio.channels,
            'sample_rate': audio.frame_rate,
            'sample_width': audio.sample_width,
            'frame_count': audio.frame_count(),
            'file_size_mb': Path(audio_path).stat().st_size / (1024 * 1024)
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def cleanup_temp_files(self, file_list: List[str]):
        """Delete temporary audio files"""
        deleted = 0
        for file_path in file_list:
            try:
                Path(file_path).unlink()
                deleted += 1
            except Exception as e:
                print(f"⚠ Could not delete {file_path}: {e}")
        
        if deleted > 0:
            print(f"✓ Cleaned up {deleted} temporary files")
    
    def adjust_speed(self, audio_path: str, speed: float = 1.0) -> AudioSegment:
        """
        Adjust playback speed without changing pitch
        
        Args:
            audio_path: Input audio file
            speed: Speed multiplier (1.0 = normal, 1.5 = 1.5x faster)
        """
        if speed == 1.0:
            return AudioSegment.from_file(audio_path)
        
        audio = AudioSegment.from_file(audio_path)
        
        # Change frame rate to adjust speed
        adjusted = audio._spawn(
            audio.raw_data,
            overrides={'frame_rate': int(audio.frame_rate * speed)}
        )
        
        # Set back to normal frame rate to maintain pitch
        return adjusted.set_frame_rate(audio.frame_rate)
