"""
PDF Parser module for extracting text from PDF files.
Combines PyPDF2 and OCR (if needed) to extract text from CVs.
"""

import os
import io
import PyPDF2
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import OCR-related packages, but make them optional
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    logger.warning("OCR packages not available. Only direct text extraction will be used.")
    OCR_AVAILABLE = False


class PDFParser:
    """PDF Parser class for extracting text from PDF files."""
    
    def __init__(self, use_ocr=True):
        """Initialize the PDF parser."""
        self.use_ocr = use_ocr and OCR_AVAILABLE
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        try:
            # First try direct text extraction
            text = self._extract_text_direct(pdf_path)
            
            # If text is too short or empty and OCR is available, try OCR
            if (not text or len(text) < 100) and self.use_ocr:
                logger.info(f"Direct extraction yielded limited text for {pdf_path}. Trying OCR...")
                text = self._extract_text_with_ocr(pdf_path)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def _extract_text_direct(self, pdf_path):
        """Extract text directly from PDF using PyPDF2."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error in direct PDF text extraction: {e}")
        
        return text.strip()
    
    def _extract_text_with_ocr(self, pdf_path):
        """Extract text from PDF using OCR when direct extraction fails."""
        if not OCR_AVAILABLE:
            logger.warning("OCR extraction requested but OCR packages are not available.")
            return ""
        
        text = ""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            # Extract text from each image
            for i, image in enumerate(images):
                # Perform OCR on the image
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
        
        return text.strip()
    
    def batch_process_directory(self, directory_path, output_directory=None):
        """
        Process all PDFs in a directory and extract text.
        
        Args:
            directory_path: Path to directory containing PDFs
            output_directory: Optional path to save text files
            
        Returns:
            Dictionary mapping filenames to extracted text
        """
        results = {}
        directory = Path(directory_path)
        
        # Create output directory if specified
        if output_directory:
            os.makedirs(output_directory, exist_ok=True)
        
        # Process each PDF file
        for pdf_file in directory.glob("*.pdf"):
            filename = pdf_file.name
            logger.info(f"Processing {filename}...")
            
            # Extract text
            text = self.extract_text_from_pdf(str(pdf_file))
            results[filename] = text
            
            # Save text to file if output directory is provided
            if output_directory and text:
                text_filepath = Path(output_directory) / f"{pdf_file.stem}.txt"
                with open(text_filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
        
        return results


# For testing purposes
if __name__ == "__main__":
    parser = PDFParser()
    
    # Test with a single file
    test_file = "AI-Powered Job Application Screening System/CVs1/C9945.pdf"
    if os.path.exists(test_file):
        text = parser.extract_text_from_pdf(test_file)
        print(f"Extracted text length: {len(text)}")
        print(f"Sample text: {text[:200]}" if text else "No text extracted.")
    else:
        print(f"Test file not found: {test_file}")
    
    # Batch process directory
    cv_directory = "AI-Powered Job Application Screening System/CVs1"
    if os.path.exists(cv_directory):
        results = parser.batch_process_directory(cv_directory)
        print(f"Processed {len(results)} PDF files.") 