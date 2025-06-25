import pytesseract
from PIL import Image
import io
import logging
import json
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
import magic

from app.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """Service for processing documents with OCR and extracting structured data."""
    
    def __init__(self):
        """Initialize OCR service with Tesseract configuration."""
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        self.supported_formats = ['image/jpeg', 'image/png', 'image/tiff', 'application/pdf']
        
        # ID document patterns for data extraction
        self.id_patterns = {
            'national_id': {
                'id_number': [
                    r'ID\s*No[:\.]?\s*([A-Z0-9]+)',
                    r'Identity\s*No[:\.]?\s*([A-Z0-9]+)',
                    r'ID\s*Number[:\.]?\s*([A-Z0-9]+)',
                    r'Card\s*No[:\.]?\s*([A-Z0-9]+)'
                ],
                'full_name': [
                    r'Name[:\.]?\s*([A-Z\s]+)',
                    r'Full\s*Name[:\.]?\s*([A-Z\s]+)',
                    r'Surname[:\.]?\s*([A-Z\s]+)'
                ],
                'date_of_birth': [
                    r'DOB[:\.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    r'Date\s*of\s*Birth[:\.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    r'Born[:\.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
                ],
                'address': [
                    r'Address[:\.]?\s*([A-Z0-9\s,.-]+)',
                    r'Residence[:\.]?\s*([A-Z0-9\s,.-]+)'
                ]
            },
            'passport': {
                'passport_number': [
                    r'Passport\s*No[:\.]?\s*([A-Z0-9]+)',
                    r'P\s*No[:\.]?\s*([A-Z0-9]+)'
                ],
                'full_name': [
                    r'Name[:\.]?\s*([A-Z\s]+)',
                    r'Surname[:\.]?\s*([A-Z\s]+)'
                ],
                'date_of_birth': [
                    r'Date\s*of\s*birth[:\.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    r'DOB[:\.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
                ],
                'nationality': [
                    r'Nationality[:\.]?\s*([A-Z\s]+)',
                    r'Country[:\.]?\s*([A-Z\s]+)'
                ]
            }
        }
    
    async def process_document(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """
        Process a document with OCR and extract structured data.
        
        Args:
            file_path: Path to the document file
            document_type: Type of document (national_id, passport, etc.)
            
        Returns:
            Dictionary containing OCR results and extracted data
        """
        try:
            # Validate file format
            mime_type = magic.from_file(file_path, mime=True)
            if mime_type not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {mime_type}")
            
            # Extract text using OCR
            ocr_text = await self._extract_text(file_path)
            
            # Extract structured data based on document type
            extracted_data = await self._extract_structured_data(ocr_text, document_type)
            
            # Calculate confidence score
            confidence = await self._calculate_confidence(ocr_text, extracted_data)
            
            return {
                'ocr_text': ocr_text,
                'extracted_data': extracted_data,
                'confidence': confidence,
                'document_type': document_type,
                'processing_status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"OCR processing failed for {file_path}: {str(e)}")
            return {
                'ocr_text': '',
                'extracted_data': {},
                'confidence': 0.0,
                'document_type': document_type,
                'processing_status': 'failed',
                'error': str(e)
            }
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from document using Tesseract OCR."""
        try:
            if file_path.lower().endswith('.pdf'):
                # For PDF files, convert to image first
                # Note: In production, you'd use pdf2image
                text = pytesseract.image_to_string(
                    Image.open(file_path),
                    lang=settings.OCR_LANGUAGES,
                    config='--psm 6'  # PSM mode for uniform text blocks
                )
            else:
                # For image files
                image = Image.open(file_path)
                # Preprocess image for better OCR results
                image = self._preprocess_image(image)
                text = pytesseract.image_to_string(
                    image,
                    lang=settings.OCR_LANGUAGES,
                    config='--psm 6'
                )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return ""
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy."""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize if too small (minimum 300 DPI equivalent)
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}")
            return image
    
    async def _extract_structured_data(self, ocr_text: str, document_type: str) -> Dict[str, Any]:
        """Extract structured data from OCR text based on document type."""
        extracted_data = {}
        
        if document_type not in self.id_patterns:
            return extracted_data
        
        patterns = self.id_patterns[document_type]
        
        # Clean OCR text
        clean_text = self._clean_ocr_text(ocr_text)
        
        # Extract each field using regex patterns
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if value:
                        extracted_data[field] = self._clean_extracted_value(value, field)
                        break
        
        # Post-process extracted data
        extracted_data = self._post_process_extracted_data(extracted_data)
        
        return extracted_data
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean OCR text to improve pattern matching."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        replacements = {
            '0': 'O',  # Zero to O in some contexts
            'l': '1',  # lowercase l to 1 in ID numbers
            'I': '1',  # uppercase I to 1 in ID numbers
        }
        
        # Apply replacements selectively
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Apply replacements only to lines that look like ID numbers
            if re.search(r'[A-Z0-9]{6,}', line):
                for old, new in replacements.items():
                    line = line.replace(old, new)
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _clean_extracted_value(self, value: str, field_type: str) -> str:
        """Clean and validate extracted values."""
        value = value.strip()
        
        if field_type in ['full_name', 'surname']:
            # Clean name fields
            value = re.sub(r'[^A-Za-z\s]', '', value)
            value = ' '.join(value.split())  # Normalize whitespace
            value = value.title()  # Proper case
            
        elif field_type in ['id_number', 'passport_number']:
            # Clean ID/passport numbers
            value = re.sub(r'[^A-Z0-9]', '', value.upper())
            
        elif field_type == 'date_of_birth':
            # Standardize date format
            value = self._standardize_date(value)
            
        elif field_type == 'address':
            # Clean address
            value = re.sub(r'\n+', ', ', value)
            value = re.sub(r'\s+', ' ', value)
            value = value.strip(', ')
        
        return value
    
    def _standardize_date(self, date_str: str) -> str:
        """Convert various date formats to YYYY-MM-DD."""
        try:
            from datetime import datetime
            
            # Common date formats
            formats = [
                '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
                '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',
                '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
                '%m/%d/%y', '%m-%d-%y', '%m.%d.%y',
                '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d'
            ]
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            return date_str  # Return original if no format matches
            
        except Exception:
            return date_str
    
    def _post_process_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process extracted data for consistency and validation."""
        processed_data = {}
        
        for key, value in data.items():
            if value and len(str(value).strip()) > 1:  # Filter out single characters
                processed_data[key] = value
        
        # Combine name fields if separated
        if 'surname' in processed_data and 'full_name' not in processed_data:
            processed_data['full_name'] = processed_data['surname']
            del processed_data['surname']
        
        return processed_data
    
    async def _calculate_confidence(self, ocr_text: str, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on OCR quality and extracted data."""
        if not ocr_text:
            return 0.0
        
        confidence_factors = []
        
        # Text length factor (longer text usually means better OCR)
        text_length_factor = min(len(ocr_text) / 500, 1.0)  # Normalize to 500 chars
        confidence_factors.append(text_length_factor * 0.3)
        
        # Extracted data factor (more fields extracted = higher confidence)
        data_factor = len(extracted_data) / 5  # Assuming max 5 fields per document
        confidence_factors.append(min(data_factor, 1.0) * 0.4)
        
        # Text quality factor (based on readable characters)
        readable_chars = len(re.sub(r'[^A-Za-z0-9\s]', '', ocr_text))
        total_chars = len(ocr_text)
        quality_factor = readable_chars / total_chars if total_chars > 0 else 0
        confidence_factors.append(quality_factor * 0.3)
        
        # Calculate final confidence score
        final_confidence = sum(confidence_factors)
        return round(min(final_confidence * 100, 100.0), 2)
    
    async def validate_document_quality(self, file_path: str) -> Dict[str, Any]:
        """Validate document quality before processing."""
        try:
            # Check file size
            file_size = Path(file_path).stat().st_size
            if file_size > settings.MAX_FILE_SIZE:
                return {
                    'valid': False,
                    'reason': 'File size exceeds maximum allowed size',
                    'max_size_mb': settings.MAX_FILE_SIZE / (1024 * 1024)
                }
            
            # Check file format
            mime_type = magic.from_file(file_path, mime=True)
            if mime_type not in self.supported_formats:
                return {
                    'valid': False,
                    'reason': f'Unsupported file format: {mime_type}',
                    'supported_formats': self.supported_formats
                }
            
            # For images, check resolution
            if mime_type.startswith('image/'):
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        if width < 300 or height < 300:
                            return {
                                'valid': False,
                                'reason': 'Image resolution too low (minimum 300x300)',
                                'current_resolution': f'{width}x{height}'
                            }
                except Exception as e:
                    return {
                        'valid': False,
                        'reason': f'Cannot read image file: {str(e)}'
                    }
            
            return {'valid': True, 'reason': 'Document quality acceptable'}
            
        except Exception as e:
            logger.error(f"Document validation failed: {str(e)}")
            return {
                'valid': False,
                'reason': f'Validation error: {str(e)}'
            }