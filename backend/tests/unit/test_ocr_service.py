import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from PIL import Image

from app.services.ocr_service import OCRService


@pytest.mark.asyncio
class TestOCRService:
    """Test OCR service functionality."""
    
    @pytest.fixture
    def ocr_service(self):
        """Create OCR service instance."""
        return OCRService()
    
    @pytest.fixture
    def sample_image_file(self):
        """Create a sample image file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Create a simple test image
            img = Image.new('RGB', (100, 100), color='white')
            img.save(tmp_file.name)
            yield tmp_file.name
            os.unlink(tmp_file.name)
    
    async def test_process_document_success(self, ocr_service, sample_image_file):
        """Test successful document processing."""
        mock_ocr_text = "ID Number: 123456789\nName: John Doe\nDOB: 01/01/1990"
        
        with patch('app.services.ocr_service.magic.from_file', return_value='image/jpeg'):
            with patch.object(ocr_service, '_extract_text', return_value=mock_ocr_text) as mock_extract:
                with patch.object(ocr_service, '_extract_structured_data') as mock_extract_data:
                    with patch.object(ocr_service, '_calculate_confidence', return_value=85.5) as mock_confidence:
                        
                        mock_extract_data.return_value = {
                            'id_number': '123456789',
                            'full_name': 'John Doe',
                            'date_of_birth': '1990-01-01'
                        }
                        
                        result = await ocr_service.process_document(sample_image_file, 'national_id')
                        
                        assert result['processing_status'] == 'completed'
                        assert result['ocr_text'] == mock_ocr_text
                        assert result['confidence'] == 85.5
                        assert result['document_type'] == 'national_id'
                        assert 'id_number' in result['extracted_data']
                        
                        mock_extract.assert_called_once_with(sample_image_file)
                        mock_extract_data.assert_called_once_with(mock_ocr_text, 'national_id')
                        mock_confidence.assert_called_once()
    
    async def test_process_document_unsupported_format(self, ocr_service, sample_image_file):
        """Test processing with unsupported file format."""
        with patch('app.services.ocr_service.magic.from_file', return_value='application/unknown'):
            result = await ocr_service.process_document(sample_image_file, 'national_id')
            
            assert result['processing_status'] == 'failed'
            assert 'Unsupported file format' in result['error']
            assert result['confidence'] == 0.0
    
    async def test_process_document_exception_handling(self, ocr_service, sample_image_file):
        """Test exception handling during document processing."""
        with patch('app.services.ocr_service.magic.from_file', side_effect=Exception("Magic error")):
            result = await ocr_service.process_document(sample_image_file, 'national_id')
            
            assert result['processing_status'] == 'failed'
            assert 'error' in result
            assert result['confidence'] == 0.0
    
    async def test_extract_text_image(self, ocr_service, sample_image_file):
        """Test text extraction from image files."""
        mock_text = "Sample OCR text"
        
        with patch('app.services.ocr_service.pytesseract.image_to_string', return_value=mock_text):
            with patch('app.services.ocr_service.Image.open') as mock_image_open:
                mock_image = MagicMock()
                mock_image_open.return_value = mock_image
                
                with patch.object(ocr_service, '_preprocess_image', return_value=mock_image) as mock_preprocess:
                    result = await ocr_service._extract_text(sample_image_file)
                    
                    assert result == mock_text
                    mock_preprocess.assert_called_once_with(mock_image)
    
    async def test_extract_text_pdf(self, ocr_service):
        """Test text extraction from PDF files."""
        pdf_file = "test.pdf"
        mock_text = "PDF OCR text"
        
        with patch('app.services.ocr_service.pytesseract.image_to_string', return_value=mock_text):
            with patch('app.services.ocr_service.Image.open') as mock_image_open:
                result = await ocr_service._extract_text(pdf_file)
                assert result == mock_text
    
    async def test_extract_text_exception(self, ocr_service, sample_image_file):
        """Test text extraction with exception."""
        with patch('app.services.ocr_service.pytesseract.image_to_string', side_effect=Exception("OCR error")):
            result = await ocr_service._extract_text(sample_image_file)
            assert result == ""
    
    def test_preprocess_image_grayscale_conversion(self, ocr_service):
        """Test image preprocessing - grayscale conversion."""
        mock_image = MagicMock()
        mock_image.mode = 'RGB'
        mock_grayscale = MagicMock()
        mock_image.convert.return_value = mock_grayscale
        mock_grayscale.size = (1200, 1200)  # Large enough to skip resizing
        
        result = ocr_service._preprocess_image(mock_image)
        
        mock_image.convert.assert_called_once_with('L')
        assert result == mock_grayscale
    
    def test_preprocess_image_resize(self, ocr_service):
        """Test image preprocessing - resizing small images."""
        mock_image = MagicMock()
        mock_image.mode = 'L'  # Already grayscale
        mock_image.size = (500, 500)  # Small image
        mock_resized = MagicMock()
        mock_image.resize.return_value = mock_resized
        
        result = ocr_service._preprocess_image(mock_image)
        
        # Should resize to at least 1000px
        mock_image.resize.assert_called_once()
        call_args = mock_image.resize.call_args[0]
        assert call_args[0][0] >= 1000  # Width should be >= 1000
        assert call_args[0][1] >= 1000  # Height should be >= 1000
    
    def test_preprocess_image_exception_handling(self, ocr_service):
        """Test image preprocessing exception handling."""
        mock_image = MagicMock()
        mock_image.convert.side_effect = Exception("Conversion error")
        
        result = ocr_service._preprocess_image(mock_image)
        assert result == mock_image  # Should return original on error
    
    async def test_extract_structured_data_national_id(self, ocr_service):
        """Test structured data extraction for national ID."""
        ocr_text = """
        ID No: 123456789
        Name: John Doe
        Date of Birth: 01/01/1990
        Address: 123 Main St
        """
        
        result = await ocr_service._extract_structured_data(ocr_text, 'national_id')
        
        assert result['id_number'] == '123456789'
        assert result['full_name'] == 'John Doe'
        assert result['date_of_birth'] == '1990-01-01'
        assert result['address'] == '123 Main St'
    
    async def test_extract_structured_data_passport(self, ocr_service):
        """Test structured data extraction for passport."""
        ocr_text = """
        Passport No: P123456789
        Surname: Smith
        Date of birth: 15/06/1985
        Nationality: American
        """
        
        result = await ocr_service._extract_structured_data(ocr_text, 'passport')
        
        assert result['passport_number'] == 'P123456789'
        assert result['full_name'] == 'Smith'
        assert result['date_of_birth'] == '1985-06-15'
        assert result['nationality'] == 'American'
    
    async def test_extract_structured_data_unknown_type(self, ocr_service):
        """Test structured data extraction for unknown document type."""
        ocr_text = "Some text"
        result = await ocr_service._extract_structured_data(ocr_text, 'unknown_type')
        assert result == {}
    
    def test_clean_ocr_text(self, ocr_service):
        """Test OCR text cleaning."""
        messy_text = "ID   Number:  \n\n  123456789  \n\n  Name: John"
        cleaned = ocr_service._clean_ocr_text(messy_text)
        
        # Should normalize whitespace
        assert "   " not in cleaned
        assert "\n\n" not in cleaned
    
    def test_clean_extracted_value_name(self, ocr_service):
        """Test cleaning name fields."""
        messy_name = "john123 doe!!!"
        cleaned = ocr_service._clean_extracted_value(messy_name, 'full_name')
        assert cleaned == "John Doe"
    
    def test_clean_extracted_value_id_number(self, ocr_service):
        """Test cleaning ID number fields."""
        messy_id = "id-123 456 789"
        cleaned = ocr_service._clean_extracted_value(messy_id, 'id_number')
        assert cleaned == "ID123456789"
    
    def test_clean_extracted_value_address(self, ocr_service):
        """Test cleaning address fields."""
        messy_address = "123\nMain\nSt\n\n\nCity"
        cleaned = ocr_service._clean_extracted_value(messy_address, 'address')
        assert cleaned == "123, Main, St, City"
    
    def test_standardize_date_various_formats(self, ocr_service):
        """Test date standardization with various formats."""
        date_tests = [
            ("01/01/1990", "1990-01-01"),
            ("1-1-90", "1990-01-01"),
            ("01.01.1990", "1990-01-01"),
            ("1990-01-01", "1990-01-01"),
            ("invalid_date", "invalid_date")  # Should return original if unparseable
        ]
        
        for input_date, expected in date_tests:
            result = ocr_service._standardize_date(input_date)
            assert result == expected
    
    def test_post_process_extracted_data(self, ocr_service):
        """Test post-processing of extracted data."""
        raw_data = {
            'surname': 'John Doe',  # Should become full_name
            'id_number': '123456789',
            'empty_field': '',  # Should be filtered out
            'single_char': 'A'  # Should be filtered out
        }
        
        processed = ocr_service._post_process_extracted_data(raw_data)
        
        assert 'full_name' in processed
        assert processed['full_name'] == 'John Doe'
        assert 'surname' not in processed
        assert 'id_number' in processed
        assert 'empty_field' not in processed
        assert 'single_char' not in processed
    
    async def test_calculate_confidence_factors(self, ocr_service):
        """Test confidence calculation with various factors."""
        # Test with good quality data
        long_text = "A" * 500  # Long text should increase confidence
        good_data = {'field1': 'value1', 'field2': 'value2', 'field3': 'value3'}
        
        confidence = await ocr_service._calculate_confidence(long_text, good_data)
        
        assert confidence > 50  # Should be reasonably high
        assert confidence <= 100
    
    async def test_calculate_confidence_empty_text(self, ocr_service):
        """Test confidence calculation with empty text."""
        confidence = await ocr_service._calculate_confidence("", {})
        assert confidence == 0.0
    
    async def test_validate_document_quality_success(self, ocr_service, sample_image_file):
        """Test document quality validation - success case."""
        with patch('app.services.ocr_service.magic.from_file', return_value='image/jpeg'):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024  # Small file size
                
                with patch('app.services.ocr_service.Image.open') as mock_image:
                    mock_img = MagicMock()
                    mock_img.size = (800, 600)  # Valid resolution
                    mock_image.return_value.__enter__.return_value = mock_img
                    
                    result = await ocr_service.validate_document_quality(sample_image_file)
                    
                    assert result['valid'] is True
                    assert result['reason'] == 'Document quality acceptable'
    
    async def test_validate_document_quality_file_too_large(self, ocr_service, sample_image_file):
        """Test document quality validation - file too large."""
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 20 * 1024 * 1024  # 20MB file
            
            result = await ocr_service.validate_document_quality(sample_image_file)
            
            assert result['valid'] is False
            assert 'File size exceeds maximum' in result['reason']
    
    async def test_validate_document_quality_unsupported_format(self, ocr_service, sample_image_file):
        """Test document quality validation - unsupported format."""
        with patch('app.services.ocr_service.magic.from_file', return_value='application/unknown'):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                
                result = await ocr_service.validate_document_quality(sample_image_file)
                
                assert result['valid'] is False
                assert 'Unsupported file format' in result['reason']
    
    async def test_validate_document_quality_low_resolution(self, ocr_service, sample_image_file):
        """Test document quality validation - low resolution."""
        with patch('app.services.ocr_service.magic.from_file', return_value='image/jpeg'):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                
                with patch('app.services.ocr_service.Image.open') as mock_image:
                    mock_img = MagicMock()
                    mock_img.size = (200, 200)  # Low resolution
                    mock_image.return_value.__enter__.return_value = mock_img
                    
                    result = await ocr_service.validate_document_quality(sample_image_file)
                    
                    assert result['valid'] is False
                    assert 'Image resolution too low' in result['reason']
                    assert 'current_resolution' in result
    
    async def test_validate_document_quality_exception(self, ocr_service, sample_image_file):
        """Test document quality validation - exception handling."""
        with patch('pathlib.Path.stat', side_effect=Exception("File error")):
            result = await ocr_service.validate_document_quality(sample_image_file)
            
            assert result['valid'] is False
            assert 'Validation error' in result['reason']


class TestOCRPatterns:
    """Test OCR pattern matching and extraction."""
    
    @pytest.fixture
    def ocr_service(self):
        return OCRService()
    
    def test_id_number_patterns(self, ocr_service):
        """Test various ID number patterns."""
        test_cases = [
            "ID No: 123456789",
            "Identity No. 987654321",
            "ID Number: ABC123456",
            "Card No: XYZ789123"
        ]
        
        for text in test_cases:
            patterns = ocr_service.id_patterns['national_id']['id_number']
            for pattern in patterns:
                import re
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    assert len(match.group(1)) > 0
                    break
            else:
                pytest.fail(f"No pattern matched text: {text}")
    
    def test_name_patterns(self, ocr_service):
        """Test various name patterns."""
        test_cases = [
            "Name: John Doe",
            "Full Name: Jane Smith",
            "Surname: Bob Johnson"
        ]
        
        for text in test_cases:
            patterns = ocr_service.id_patterns['national_id']['full_name']
            for pattern in patterns:
                import re
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    assert len(match.group(1).strip()) > 0
                    break
            else:
                pytest.fail(f"No pattern matched text: {text}")
    
    def test_date_patterns(self, ocr_service):
        """Test various date patterns."""
        test_cases = [
            "DOB: 01/01/1990",
            "Date of Birth: 15-06-1985",
            "Born: 31.12.1975"
        ]
        
        for text in test_cases:
            patterns = ocr_service.id_patterns['national_id']['date_of_birth']
            for pattern in patterns:
                import re
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    assert len(match.group(1)) > 0
                    break
            else:
                pytest.fail(f"No pattern matched text: {text}")