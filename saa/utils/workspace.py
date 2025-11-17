"""
Workspace utilities for managing temp directories and staged processing
"""
from pathlib import Path
from typing import Optional
import shutil
import json
import logging

from saa.constants import TEMP_DIR_NAME

logger = logging.getLogger(__name__)


class WorkspaceManager:
    """
    Manages the .temp directory structure for staged audiobook processing.
    
    Directory Structure:
        .temp/
            extracted/      - Raw extracted text from PDF/TXT
            staged/         - Cleaned chunks with voice metadata (JSON)
            voices/         - Generated audio chunks (WAV files)
    """
    
    def __init__(self, base_path: Path = None):
        """
        Initialize workspace manager.
        
        Args:
            base_path: Base directory (defaults to cwd/output)
        """
        if base_path is None:
            base_path = Path.cwd() / "output"
        
        self.base_path = Path(base_path)
        self.temp_root = self.base_path / TEMP_DIR_NAME
        
        # Define stage directories
        self.extracted_dir = self.temp_root / "extracted"
        self.staged_dir = self.temp_root / "staged"
        self.voices_dir = self.temp_root / "voices"
    
    def setup(self) -> None:
        """Create all temp directories if they don't exist."""
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        self.staged_dir.mkdir(parents=True, exist_ok=True)
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[Workspace] Initialized temp structure at: {self.temp_root}")
    
    def cleanup(self) -> None:
        """Delete all files in temp directories, keep structure intact."""
        for directory in [self.extracted_dir, self.staged_dir, self.voices_dir]:
            if directory.exists():
                for file_path in directory.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                        logger.debug(f"[Workspace] Deleted: {file_path.name}")
        
        logger.info("[Workspace] Cleaned up temp directories")
    
    def clear_all(self) -> None:
        """Delete entire temp directory structure."""
        if self.temp_root.exists():
            shutil.rmtree(self.temp_root)
            logger.info(f"[Workspace] Removed temp directory: {self.temp_root}")
    
    # File path helpers
    def get_extracted_text_path(self) -> Path:
        """Get path for extracted text file."""
        return self.extracted_dir / "extracted.txt"
    
    def get_chunks_json_path(self) -> Path:
        """Get path for staged chunks JSON file."""
        return self.staged_dir / "chunks.json"
    
    def get_voice_chunk_path(self, chunk_id: int) -> Path:
        """Get path for voice chunk audio file."""
        return self.voices_dir / f"chunk_{chunk_id:04d}.wav"
    
    def get_all_voice_chunks(self) -> list[Path]:
        """Get all voice chunk files sorted by chunk ID."""
        chunks = sorted(self.voices_dir.glob("chunk_*.wav"))
        return chunks
    
    # JSON helpers
    def save_chunks_json(self, chunks: list[dict]) -> Path:
        """
        Save chunks to JSON file.
        
        Args:
            chunks: List of chunk dictionaries with {id, text, voice, speed, emotion}
            
        Returns:
            Path to the saved JSON file
        """
        json_path = self.get_chunks_json_path()
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"chunks": chunks}, f, indent=2, ensure_ascii=False)
        logger.info(f"[Workspace] Saved {len(chunks)} chunks to: {json_path}")
        return json_path
    
    def load_chunks_json(self) -> list[dict]:
        """
        Load chunks from JSON file.
        
        Returns:
            List of chunk dictionaries
        """
        json_path = self.get_chunks_json_path()
        if not json_path.exists():
            raise FileNotFoundError(f"Chunks JSON not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get("chunks", [])
        logger.info(f"[Workspace] Loaded {len(chunks)} chunks from: {json_path}")
        return chunks
    
    def save_extracted_text(self, text: str) -> Path:
        """
        Save extracted text to file.
        
        Args:
            text: Extracted text content
            
        Returns:
            Path to the saved text file
        """
        text_path = self.get_extracted_text_path()
        text_path.write_text(text, encoding='utf-8')
        logger.info(f"[Workspace] Saved extracted text ({len(text)} chars) to: {text_path}")
        return text_path
    
    def load_extracted_text(self) -> str:
        """Load extracted text from file."""
        text_path = self.get_extracted_text_path()
        if not text_path.exists():
            raise FileNotFoundError(f"Extracted text not found: {text_path}")
        
        text = text_path.read_text(encoding='utf-8')
        logger.info(f"[Workspace] Loaded extracted text ({len(text)} chars) from: {text_path}")
        return text
