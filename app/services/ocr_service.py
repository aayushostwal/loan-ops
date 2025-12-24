"""
OCR Service Module

Handles PDF document reading and OCR text extraction using Tesseract.
"""
import logging
import tempfile
from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# Configure logging
logger = logging.getLogger(__name__)


class OCRService:
    """
    Service class for OCR operations on PDF documents.
    
    This service uses PyMuPDF to convert PDF pages to images,
    and pytesseract for OCR text extraction.
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR Service
        
        Args:
            tesseract_cmd: Optional path to tesseract executable.
                          If None, uses system default.
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        logger.info("OCR Service initialized")
    
    async def extract_text_from_pdf(
        self, 
        pdf_bytes: bytes,
        dpi: int = 300,
        language: str = 'eng'
    ) -> str:
        """
        Extract text from PDF using OCR.
        
        Args:
            pdf_bytes: PDF file content as bytes
            dpi: DPI resolution for image conversion (default: 300)
            language: Tesseract language code (default: 'eng')
        
        Returns:
            str: Extracted text from all pages
            
        Raises:
            ValueError: If PDF is empty or invalid
            RuntimeError: If OCR processing fails
        """
        try:
            logger.info(f"Starting OCR extraction, DPI={dpi}, Language={language}")
            
            # Validate input
            if not pdf_bytes:
                logger.error("Empty PDF bytes provided")
                raise ValueError("PDF content is empty")
            
            # Open PDF from bytes using PyMuPDF
            logger.debug("Opening PDF with PyMuPDF...")
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            if pdf_document.page_count == 0:
                logger.error("PDF has no pages")
                raise ValueError("PDF document is empty")
            
            logger.info(f"Successfully opened PDF with {pdf_document.page_count} page(s)")
            
            # Extract text from each page
            extracted_texts = []
            
            # Calculate zoom factor for DPI
            # PyMuPDF uses a matrix for scaling. Default is 72 DPI.
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                logger.debug(f"Processing page {page_num + 1}/{pdf_document.page_count}")
                
                # Convert page to image (pixmap)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert pixmap to PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # Perform OCR on the image
                text = pytesseract.image_to_string(
                    image,
                    lang=language,
                    config='--psm 1'  # Automatic page segmentation with OSD
                )
                
                if text.strip():
                    extracted_texts.append(f"--- Page {page_num + 1} ---\n{text}")
                    logger.debug(f"Page {page_num + 1}: Extracted {len(text)} characters")
                else:
                    logger.warning(f"Page {page_num + 1}: No text extracted")
            
            # Close the PDF document
            pdf_document.close()
            
            # Combine all pages
            full_text = "\n\n".join(extracted_texts)
            
            logger.info(
                f"OCR extraction completed successfully. "
                f"Total characters: {len(full_text)}"
            )
            
            return full_text
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"OCR processing failed: {str(e)}") from e
    
    async def extract_text_from_image(
        self,
        image_bytes: bytes,
        language: str = 'eng'
    ) -> str:
        """
        Extract text from a single image using OCR.
        
        Args:
            image_bytes: Image file content as bytes
            language: Tesseract language code (default: 'eng')
        
        Returns:
            str: Extracted text
        """
        try:
            logger.info("Starting OCR extraction from image")
            
            # Open image from bytes
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            
            try:
                image = Image.open(tmp_path)
                
                # Perform OCR
                text = pytesseract.image_to_string(image, lang=language)
                
                logger.info(f"Image OCR completed. Extracted {len(text)} characters")
                return text
                
            finally:
                # Cleanup temporary file
                Path(tmp_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Image OCR failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Image OCR processing failed: {str(e)}") from e
    
    def validate_tesseract_installation(self) -> bool:
        """
        Check if Tesseract is properly installed and accessible.
        
        Returns:
            bool: True if Tesseract is available
        """
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
            return True
        except Exception as e:
            logger.error(f"Tesseract not found: {str(e)}")
            return False
