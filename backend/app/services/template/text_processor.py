"""
Text processing service for uploaded template files
Handles text extraction from various file formats and preprocessing
"""

import io
import re
import hashlib
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import file processing libraries
try:
    import textract
except ImportError:
    textract = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from app.models.template import FileFormat

logger = logging.getLogger(__name__)


class TextProcessor:
    """Service for processing uploaded template files"""
    
    def __init__(self):
        self.supported_formats = {
            FileFormat.TXT: self._extract_text_from_txt,
            FileFormat.HTML: self._extract_text_from_html,
            FileFormat.MD: self._extract_text_from_markdown,
        }
        
        # Add support for additional formats if libraries are available
        if Document:
            self.supported_formats[FileFormat.DOCX] = self._extract_text_from_docx
        
        if PyPDF2:
            self.supported_formats[FileFormat.PDF] = self._extract_text_from_pdf
    
    def calculate_file_hash(self, content: bytes) -> str:
        """
        Calculate SHA-256 hash of file content
        
        Args:
            content: File content as bytes
            
        Returns:
            str: SHA-256 hash
        """
        return hashlib.sha256(content).hexdigest()
    
    def extract_text(self, content: bytes, file_format: FileFormat) -> str:
        """
        Extract text from file content
        
        Args:
            content: File content as bytes
            file_format: Format of the file
            
        Returns:
            str: Extracted text
            
        Raises:
            ValueError: If file format is not supported
            Exception: If extraction fails
        """
        if file_format not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        try:
            extractor = self.supported_formats[file_format]
            text = extractor(content)
            
            # Basic cleanup
            return self._clean_text(text)
            
        except Exception as e:
            logger.error(f"Failed to extract text from {file_format} file: {e}")
            raise Exception(f"Text extraction failed: {e}")
    
    def _extract_text_from_txt(self, content: bytes) -> str:
        """Extract text from plain text file"""
        try:
            # Try UTF-8 first, fallback to latin-1
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('latin-1', errors='ignore')
        except Exception as e:
            raise Exception(f"Failed to decode text file: {e}")
    
    def _extract_text_from_html(self, content: bytes) -> str:
        """Extract text from HTML file"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            # Fallback: basic HTML tag removal
            text = content.decode('utf-8', errors='ignore')
            text = re.sub('<[^<]+?>', '', text)
            return text
        
        try:
            text = content.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            return soup.get_text()
        except Exception as e:
            raise Exception(f"Failed to extract text from HTML: {e}")
    
    def _extract_text_from_markdown(self, content: bytes) -> str:
        """Extract text from Markdown file"""
        try:
            text = content.decode('utf-8', errors='ignore')
            
            # Remove markdown syntax (basic cleanup)
            # Remove headers
            text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
            # Remove bold/italic
            text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
            text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
            # Remove links
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            # Remove code blocks
            text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
            text = re.sub(r'`([^`]+)`', r'\1', text)
            
            return text
        except Exception as e:
            raise Exception(f"Failed to extract text from Markdown: {e}")
    
    def _extract_text_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX file"""
        if not Document:
            raise Exception("python-docx library not available")
        
        try:
            doc = Document(io.BytesIO(content))
            text_parts = []
            
            for paragraph in doc.paragraphs:
                text_parts.append(paragraph.text)
            
            return '\n'.join(text_parts)
        except Exception as e:
            raise Exception(f"Failed to extract text from DOCX: {e}")
    
    def _extract_text_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF file"""
        if not PyPDF2:
            raise Exception("PyPDF2 library not available")
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_parts = []
            
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())
            
            return '\n'.join(text_parts)
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {e}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove non-printable characters (except common ones)
        text = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\x80-\xFF]', '', text)
        
        return text
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Get basic statistics about the text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with text statistics
        """
        if not text:
            return {
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "avg_sentence_length": 0,
                "character_count": 0
            }
        
        # Count words
        words = text.split()
        word_count = len(words)
        
        # Count sentences (basic)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        # Count paragraphs
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Average sentence length
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "avg_sentence_length": round(avg_sentence_length, 2),
            "character_count": len(text)
        }
    
    def validate_file_content(self, content: bytes, file_format: FileFormat) -> Dict[str, Any]:
        """
        Validate file content and return validation results
        
        Args:
            content: File content as bytes
            file_format: Expected file format
            
        Returns:
            Dict with validation results
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "file_size": len(content),
            "format": file_format.value
        }
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            result["is_valid"] = False
            result["errors"].append(f"File size ({len(content)} bytes) exceeds maximum allowed size ({max_size} bytes)")
        
        # Check minimum size (100 bytes)
        min_size = 100
        if len(content) < min_size:
            result["is_valid"] = False
            result["errors"].append(f"File size ({len(content)} bytes) is too small (minimum {min_size} bytes)")
        
        # Try to extract text to validate format
        try:
            extracted_text = self.extract_text(content, file_format)
            
            if not extracted_text.strip():
                result["is_valid"] = False
                result["errors"].append("No readable text could be extracted from the file")
            elif len(extracted_text.strip()) < 50:
                result["warnings"].append("Very little text extracted - file may not contain much content")
                
            # Check if text looks like a fantasy football recap
            text_lower = extracted_text.lower()
            fantasy_indicators = [
                'fantasy', 'football', 'nfl', 'recap', 'week', 'points', 'score', 
                'team', 'player', 'touchdown', 'quarterback', 'running back'
            ]
            
            found_indicators = sum(1 for indicator in fantasy_indicators if indicator in text_lower)
            if found_indicators < 2:
                result["warnings"].append("Text may not be a fantasy football recap")
                
        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"Failed to extract text: {str(e)}")
        
        return result


# Global instance
text_processor = TextProcessor()
