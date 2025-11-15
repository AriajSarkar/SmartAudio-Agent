"""
PDF and TXT Text Extraction and Processing Module
Supports both PDF and TXT files for audiobook generation
"""
import re
import PyPDF2
import pdfplumber
from pathlib import Path
from typing import List, Dict, Optional
from config import PDF_CONFIG


class DocumentProcessor:
    """Extract and clean text from PDF or TXT files"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.file_type = self.file_path.suffix.lower()
        if self.file_type not in ['.pdf', '.txt']:
            raise ValueError(f"Unsupported file type: {self.file_type}. Only PDF and TXT are supported.")
        
        self.text = ""
        self.pages = []
        self.metadata = {}
    
    def extract_text(self, use_pdfplumber: bool = True) -> str:
        """
        Extract text from PDF or TXT file
        """
        if self.file_type == '.txt':
            return self._extract_from_txt()
        else:  # .pdf
            if use_pdfplumber:
                return self._extract_with_pdfplumber()
            else:
                return self._extract_with_pypdf2()
    
    def _extract_from_txt(self) -> str:
        """Extract text from TXT file"""
        try:
            # Try UTF-8 first
            with open(self.file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            # Fallback to other encodings
            try:
                with open(self.file_path, 'r', encoding='latin-1') as f:
                    text = f.read()
            except:
                with open(self.file_path, 'r', encoding='cp1252') as f:
                    text = f.read()
        
        # Clean the text
        cleaned = self._clean_text(text)
        
        # Split into pages (every 500 words = 1 "page" for consistency)
        words = cleaned.split()
        page_size = 500
        
        for i in range(0, len(words), page_size):
            page_text = ' '.join(words[i:i + page_size])
            self.pages.append({
                'number': (i // page_size) + 1,
                'text': page_text
            })
        
        self.text = cleaned
        return self.text
    
    def _extract_with_pdfplumber(self) -> str:
        """Extract text using pdfplumber (better for complex PDFs)"""
        all_text = []
        
        with pdfplumber.open(self.file_path) as pdf:
            self.metadata = pdf.metadata or {}
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    cleaned = self._clean_page_text(text, page_num)
                    self.pages.append({
                        'number': page_num,
                        'text': cleaned
                    })
                    all_text.append(cleaned)
        
        self.text = "\n\n".join(all_text)
        return self.text
    
    def _extract_with_pypdf2(self) -> str:
        """Extract text using PyPDF2 (faster, simpler)"""
        all_text = []
        
        with open(self.file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            self.metadata = pdf_reader.metadata or {}
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text:
                    cleaned = self._clean_page_text(text, page_num)
                    self.pages.append({
                        'number': page_num,
                        'text': cleaned
                    })
                    all_text.append(cleaned)
        
        self.text = "\n\n".join(all_text)
        return self.text
    
    def _clean_page_text(self, text: str, page_num: int) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers if configured
        if PDF_CONFIG['remove_page_numbers']:
            # Common page number patterns
            text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'Page\s+\d+', '', text, flags=re.IGNORECASE)
        
        # Fix common OCR issues
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        text = text.replace('–', '-').replace('—', '-')
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _clean_text(self, text: str) -> str:
        """Clean text from TXT files"""
        # Remove excessive whitespace while preserving paragraphs
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Fix common encoding issues
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        return text.strip()
    
    def get_sample_text(self, length: int = 1000) -> str:
        """Get first N characters for sample generation"""
        if not self.text:
            self.extract_text()
        
        return self.text[:length].strip()
    
    def get_paragraphs(self, num_paragraphs: int = None) -> List[str]:
        """Split text into paragraphs"""
        if not self.text:
            self.extract_text()
        
        # Split by double newlines or paragraph markers
        paragraphs = re.split(r'\n\s*\n+', self.text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if num_paragraphs:
            return paragraphs[:num_paragraphs]
        
        return paragraphs
    
    def get_chunks(self, chunk_size: int = None) -> List[str]:
        """
        Split text into chunks for TTS processing
        Respects sentence boundaries
        """
        if not self.text:
            self.extract_text()
        
        chunk_size = chunk_size or PDF_CONFIG['chunk_size']
        
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', self.text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def get_info(self) -> Dict:
        """Get file metadata and statistics"""
        if not self.text:
            self.extract_text()
        
        file_type_name = "PDF" if self.file_type == '.pdf' else "Text File"
        
        return {
            'filename': self.file_path.name,
            'file_type': file_type_name,
            'pages': len(self.pages),
            'total_characters': len(self.text),
            'total_words': len(self.text.split()),
            'estimated_duration_minutes': len(self.text.split()) / 150,  # Average reading speed
            'metadata': self.metadata
        }


# Keep backward compatibility
PDFProcessor = DocumentProcessor
