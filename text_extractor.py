"""
Text Extraction Module for LAFO
Handles PDF text extraction, image OCR, and document content parsing.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple
import pytesseract
from PIL import Image

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from config import TESSERACT_PATH, OCR_LANGUAGE, MAX_FILE_SIZE

logger = logging.getLogger(__name__)

# Set Tesseract path for Windows
try:
    pytesseract.pytesseract.pytesseract_cmd = TESSERACT_PATH
except Exception as e:
    logger.warning(f"Tesseract path not configured: {str(e)}")

class TextExtractor:
    """Extracts text content from various file formats."""
    
    @staticmethod
    def extract_from_pdf(file_path: str) -> Tuple[str, bool]:
        """
        Extract text from PDF files.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            if not pdfplumber:
                logger.warning("pdfplumber not installed, skipping PDF extraction")
                return "", False
            
            file_size = Path(file_path).stat().st_size
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"File too large ({file_size} bytes): {file_path}")
                return "", False
            
            text_content = []
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"  📄 Extracting text from {total_pages} pages...")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        if text:
                            text_content.append(f"--- Page {page_num} ---\n{text}")
                    except Exception as e:
                        logger.debug(f"Error extracting page {page_num}: {str(e)}")
                        # Try OCR fallback for this page
                        try:
                            img = page.to_image()
                            ocr_text = TextExtractor._ocr_image(img.original)
                            if ocr_text:
                                text_content.append(f"--- Page {page_num} (OCR) ---\n{ocr_text}")
                        except Exception as ocr_error:
                            logger.debug(f"OCR fallback also failed: {str(ocr_error)}")
            
            full_text = "\n\n".join(text_content)
            if full_text.strip():
                logger.info(f"  ✅ Extracted {len(full_text)} characters from PDF")
                return full_text, True
            else:
                logger.warning("PDF has no extractable text, trying OCR...")
                return TextExtractor._extract_pdf_with_ocr(file_path)
        
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return "", False
    
    @staticmethod
    def _extract_pdf_with_ocr(file_path: str) -> Tuple[str, bool]:
        """
        Extract text from PDF using OCR as fallback.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            if not pdfplumber:
                return "", False
            
            text_content = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        img = page.to_image().original
                        ocr_text = TextExtractor._ocr_image(img)
                        if ocr_text:
                            text_content.append(f"--- Page {page_num} (OCR) ---\n{ocr_text}")
                    except Exception as e:
                        logger.debug(f"OCR failed for page {page_num}: {str(e)}")
            
            full_text = "\n\n".join(text_content)
            return full_text, len(full_text) > 0
        
        except Exception as e:
            logger.error(f"OCR fallback failed: {str(e)}")
            return "", False
    
    @staticmethod
    def extract_from_image(file_path: str) -> Tuple[str, bool]:
        """
        Extract text from image files using OCR.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            logger.info(f"  🖼️  Extracting text from image using OCR...")
            img = Image.open(file_path)
            text = TextExtractor._ocr_image(img)
            
            if text.strip():
                logger.info(f"  ✅ Extracted {len(text)} characters from image")
                return text, True
            else:
                logger.warning(f"No text found in image: {file_path}")
                return "", False
        
        except Exception as e:
            logger.error(f"Error extracting image text: {str(e)}")
            return "", False
    
    @staticmethod
    def _ocr_image(image) -> str:
        """
        Perform OCR on an image object.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text
        """
        try:
            text = pytesseract.image_to_string(image, lang=OCR_LANGUAGE)
            return text if text else ""
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            return ""
    
    @staticmethod
    def extract_from_text(file_path: str) -> Tuple[str, bool]:
        """
        Extract content from plain text files.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Tuple of (file_content, success)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.strip():
                logger.info(f"  ✅ Loaded {len(content)} characters from text file")
                return content, True
            else:
                logger.warning(f"Text file is empty: {file_path}")
                return "", False
        
        except Exception as e:
            logger.error(f"Error reading text file: {str(e)}")
            return "", False
    
    @staticmethod
    def extract_from_docx(file_path: str) -> Tuple[str, bool]:
        """
        Extract text from Word documents.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            from docx import Document as DocxDocument
            
            doc = DocxDocument(file_path)
            text_content = "\n".join([para.text for para in doc.paragraphs])
            
            if text_content.strip():
                logger.info(f"  ✅ Extracted {len(text_content)} characters from DOCX")
                return text_content, True
            else:
                logger.warning(f"DOCX file has no text: {file_path}")
                return "", False
        
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            return "", False
    
    @staticmethod
    def extract_from_html(file_path: str) -> Tuple[str, bool]:
        """
        Extract text from HTML files.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            from html.parser import HTMLParser
            
            class TextParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                
                def handle_data(self, data):
                    text = data.strip()
                    if text:
                        self.text.append(text)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            parser = TextParser()
            parser.feed(html_content)
            text = ' '.join(parser.text)
            
            if text.strip():
                logger.info(f"  ✅ Extracted {len(text)} characters from HTML")
                return text, True
            else:
                logger.warning(f"HTML file has no text: {file_path}")
                return "", False
        
        except Exception as e:
            logger.error(f"Error extracting HTML text: {str(e)}")
            return "", False
    
    @staticmethod
    def extract_content(file_path: str) -> Tuple[str, bool]:
        """
        Intelligently extract text content from any supported file type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (extracted_text, success)
        """
        file_path = str(file_path).lower()
        
        logger.info(f"Extracting content from: {Path(file_path).name}")
        
        if file_path.endswith('.pdf'):
            return TextExtractor.extract_from_pdf(file_path)
        elif file_path.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            return TextExtractor.extract_from_image(file_path)
        elif file_path.endswith(('.docx', '.doc')):
            return TextExtractor.extract_from_docx(file_path)
        elif file_path.endswith('.html'):
            return TextExtractor.extract_from_html(file_path)
        elif file_path.endswith('.txt'):
            return TextExtractor.extract_from_text(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return "", False
