"""
Audio processing tools (ADK function tools)
Merge, normalize, and export audio files with ffmpeg support
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydub import AudioSegment
from pydub.utils import which
import subprocess
import tempfile

from saa.exceptions import AudioProcessingError, AudioMergeError


def merge_audio_chunks(
    audio_files: List[str],
    output_path: str,
    crossfade_ms: int = 0,
    use_ffmpeg: bool = True,
    cleanup_chunks: bool = True
) -> Dict[str, Any]:
    """
    Merge multiple audio chunks into a single file using ffmpeg (lossless).
    
    Uses ffmpeg concat for fast, lossless merging. Automatically cleans up
    temp directory after successful merge.
    
    Args:
        audio_files: List of audio file paths (must be WAV format)
        output_path: Path for merged output file
        crossfade_ms: Crossfade duration (0 = disabled, requires pydub fallback)
        use_ffmpeg: Use ffmpeg concat (faster, lossless) vs pydub
        cleanup_chunks: Delete chunk files after merge
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - output_file: Path to merged audio
            - total_chunks: Number of chunks merged
            - file_size_mb: Output file size
            - method: "ffmpeg_concat" or "pydub"
            - chunks_deleted: Number of chunks cleaned up
    """
    try:
        if not audio_files:
            raise AudioMergeError("No audio files to merge")
        
        # Verify all files exist
        missing = [f for f in audio_files if not Path(f).exists()]
        if missing:
            raise AudioMergeError(f"Missing audio files: {missing}")
        
        # Ensure output directory exists
        output_path_obj = Path(output_path)
        if not output_path_obj.is_absolute():
            output_path_obj = Path.cwd() / "output" / output_path_obj.name
        
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        method = "unknown"
        
        # Try ffmpeg concat first (faster, lossless)
        if use_ffmpeg and crossfade_ms == 0:
            ffmpeg_path = which("ffmpeg")
            if ffmpeg_path:
                try:
                    # Create temporary file list for ffmpeg concat
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                        for audio_file in audio_files:
                            abs_path = Path(audio_file).resolve()
                            safe_path = str(abs_path).replace("'", "'\\''")
                            f.write(f"file '{safe_path}'\n")
                        filelist_path = f.name
                    
                    try:
                        # Run ffmpeg concat (lossless, no re-encoding)
                        cmd = [
                            ffmpeg_path,
                            '-f', 'concat',
                            '-safe', '0',
                            '-i', filelist_path,
                            '-c', 'copy',  # No re-encoding
                            '-y',  # Overwrite
                            str(output_path_obj)
                        ]
                        
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        method = "ffmpeg_concat"
                        
                    finally:
                        # Cleanup temp file list
                        try:
                            Path(filelist_path).unlink()
                        except Exception:
                            pass
                            
                except Exception as e:
                    # Fallback to pydub if ffmpeg fails
                    use_ffmpeg = False
        
        # Fallback: Use pydub (slower, re-encodes, but supports crossfade)
        if not use_ffmpeg or crossfade_ms > 0:
            combined = AudioSegment.from_wav(audio_files[0])
            
            for audio_file in audio_files[1:]:
                next_segment = AudioSegment.from_wav(audio_file)
                
                if crossfade_ms > 0:
                    combined = combined.append(next_segment, crossfade=crossfade_ms)
                else:
                    combined = combined + next_segment
            
            combined.export(str(output_path_obj), format="wav")
            method = "pydub" + ("_crossfade" if crossfade_ms > 0 else "")
        
        # Get file info
        file_size = output_path_obj.stat().st_size / (1024 * 1024)  # MB
        
        # Clean up temp directory and chunks
        chunks_deleted = 0
        if cleanup_chunks:
            for audio_file in audio_files:
                try:
                    chunk_path = Path(audio_file)
                    if chunk_path.exists():
                        chunk_path.unlink()
                        chunks_deleted += 1
                except Exception:
                    pass
            
            # Try to remove temp directory if empty
            try:
                for audio_file in audio_files:
                    temp_dir = Path(audio_file).parent
                    if temp_dir.name == ".temp" and temp_dir.exists():
                        if not any(temp_dir.iterdir()):
                            temp_dir.rmdir()
                        break
            except Exception:
                pass
        
        return {
            "status": "success",
            "output_file": str(output_path_obj),
            "total_chunks": len(audio_files),
            "file_size_mb": round(file_size, 2),
            "method": method,
            "chunks_deleted": chunks_deleted,
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "output_file": "",
            "total_chunks": 0,
            "file_size_mb": 0,
            "method": "failed",
            "chunks_deleted": 0,
            "error": str(e)
        }


def normalize_audio(
    input_file: str,
    target_dbfs: float = -20.0
) -> Dict[str, Any]:
    """
    Normalize audio volume to target level.
    
    Adjusts audio loudness to consistent level using RMS normalization.
    Prevents volume variations between different TTS segments.
    
    Args:
        input_file: Path to audio file
        target_dbfs: Target loudness in dBFS (default: -20.0)
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - output_file: Path to normalized audio (overwrites input)
            - original_dbfs: Original loudness level
            - normalized_dbfs: New loudness level
            - change_db: Adjustment applied
    """
    try:
        path = Path(input_file)
        
        if not path.exists():
            raise AudioProcessingError(f"Audio file not found: {input_file}")
        
        # Load audio
        audio = AudioSegment.from_file(str(path))
        
        # Get original loudness
        original_dbfs = audio.dBFS
        
        # Calculate required change
        change_db = target_dbfs - original_dbfs
        
        # Apply normalization
        normalized = audio.apply_gain(change_db)
        
        # Overwrite original file
        normalized.export(str(path), format=path.suffix[1:])
        
        return {
            "status": "success",
            "output_file": str(path),
            "original_dbfs": round(original_dbfs, 2),
            "normalized_dbfs": round(target_dbfs, 2),
            "change_db": round(change_db, 2),
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "output_file": "",
            "error": str(e)
        }


def export_audio_format(
    input_file: str,
    output_file: str,
    format: str = "mp3",
    quality: str = "high"
) -> Dict[str, Any]:
    """
    Export audio to different format with quality settings.
    
    Converts audio between formats (WAV, MP3, OGG, FLAC) with
    configurable quality. Requires FFmpeg for MP3/OGG export.
    
    Args:
        input_file: Path to source audio file
        output_file: Path for output file
        format: Output format (mp3/wav/ogg/flac)
        quality: Quality preset (low/medium/high)
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - output_file: Path to exported file
            - format: Output format
            - file_size_mb: Output file size
            - compression_ratio: Size reduction vs input
    """
    try:
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        # Ensure paths are in output directory
        if not input_path.is_absolute():
            input_path = Path.cwd() / "output" / input_path.name
        if not output_path.is_absolute():
            output_path = Path.cwd() / "output" / output_path.name
        
        if not input_path.exists():
            raise AudioProcessingError(f"Input file not found: {input_file}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load audio
        audio = AudioSegment.from_file(str(input_path))
        
        # Set export parameters based on format and quality
        export_params = {"format": format}
        
        if format == "mp3":
            # Check for FFmpeg
            if not which("ffmpeg"):
                return {
                    "status": "error",
                    "error": "FFmpeg not found. Required for MP3 export. "
                            "Download from https://ffmpeg.org/"
                }
            
            quality_map = {
                "low": "9",    # ~64 kbps
                "medium": "5",  # ~128 kbps
                "high": "2"     # ~192 kbps
            }
            export_params["parameters"] = ["-q:a", quality_map.get(quality, "2")]
        
        elif format == "wav":
            export_params["parameters"] = [
                "-ar", "24000",  # Sample rate
                "-ac", "1"       # Mono
            ]
        
        # Export
        audio.export(str(output_path), **export_params)
        
        # Calculate stats
        input_size = input_path.stat().st_size / (1024 * 1024)
        output_size = output_path.stat().st_size / (1024 * 1024)
        compression_ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0
        
        # Clean up intermediate WAV file after conversion to final format
        # Delete WAV file if we're converting to a different format (MP3, OGG, etc.)
        # and the WAV has the same base name as output (e.g., sample.wav → sample.mp3)
        if format != "wav" and input_path.suffix == ".wav":
            try:
                # Check if it's an intermediate file by comparing base names
                input_base = input_path.stem  # e.g., "sample" from "sample.wav"
                output_base = output_path.stem  # e.g., "sample" from "sample.mp3"
                
                # Delete if same base name (intermediate) or known temp file
                if input_base == output_base or input_path.name in ["merged.wav", "normalized.wav", "temp.wav"]:
                    input_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors
        
        return {
            "status": "success",
            "output_file": str(output_path),
            "format": format,
            "file_size_mb": round(output_size, 2),
            "compression_ratio": round(compression_ratio, 2),
            "cleaned_intermediate": input_path.name if format != "wav" else None,
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "output_file": "",
            "format": format,
            "error": str(e)
        }


def get_audio_info(audio_file: str) -> Dict[str, Any]:
    """
    Get detailed information about an audio file.
    
    Extracts metadata, duration, and technical specs from audio file.
    Useful for validation and progress reporting.
    
    Args:
        audio_file: Path to audio file
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - duration_seconds: Audio duration
            - duration_formatted: Duration as HH:MM:SS
            - channels: Number of channels
            - sample_rate: Sample rate in Hz
            - frame_rate: Frame rate
            - file_size_mb: File size in megabytes
            - format: File format
    """
    try:
        path = Path(audio_file)
        
        if not path.exists():
            raise AudioProcessingError(f"Audio file not found: {audio_file}")
        
        # Load audio
        audio = AudioSegment.from_file(str(path))
        
        # Extract information
        duration_ms = len(audio)
        duration_seconds = duration_ms / 1000.0
        
        # Format duration as HH:MM:SS
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        
        if hours > 0:
            duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            duration_formatted = f"{minutes:02d}:{seconds:02d}"
        
        file_size = path.stat().st_size / (1024 * 1024)
        
        return {
            "status": "success",
            "duration_seconds": round(duration_seconds, 2),
            "duration_formatted": duration_formatted,
            "channels": audio.channels,
            "sample_rate": audio.frame_rate,
            "frame_rate": audio.frame_rate,
            "file_size_mb": round(file_size, 2),
            "format": path.suffix[1:],
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "duration_seconds": 0,
            "duration_formatted": "00:00",
            "error": str(e)
        }
