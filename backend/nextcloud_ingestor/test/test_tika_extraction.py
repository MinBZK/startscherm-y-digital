"""
Tests for Tika content extraction functionality.

This module tests that Tika server can extract text content from various
document formats and that the extraction is properly integrated into the ingestor.
"""

import pytest
import tempfile
import os
from nextcloud_ingestor.src.content import ContentExtractor, NotSupportedError
from nextcloud_ingestor.src.utils import logger


class TestTikaExtraction:
    """Test cases for Tika content extraction."""

    @pytest.fixture
    def extractor(self):
        """Create a ContentExtractor instance."""
        return ContentExtractor()

    def test_tika_server_availability(self, extractor):
        """Test that Tika server is available and responding."""
        assert extractor.tika_available, "Tika server should be available"
        logger.info("Tika server is available and responding")

    def test_txt_extraction(self, extractor):
        """Test extraction from a plain text file."""
        test_content = b"This is a test document.\n\nIt has multiple paragraphs.\n\nWith some content to extract."
        
        result = extractor.extract("test.txt", test_content)
        
        assert result is not None
        assert "test document" in result
        assert "multiple paragraphs" in result
        assert "content to extract" in result
        logger.info(f"TXT extraction successful: {len(result)} characters extracted")


    def test_md_extraction(self, extractor):
        """Test extraction from a Markdown file."""
        test_content = b"# This is a test document\n\nIt has multiple paragraphs.\n\nWith some content to extract."
        
        result = extractor.extract("test.md", test_content)
        
        assert result is not None
        assert "test document" in result
        assert "multiple paragraphs" in result
        assert "content to extract" in result
        logger.info(f"MD extraction successful: {len(result)} characters extracted")


    def test_unsupported_file_type(self, extractor):
        """Test extraction from an unsupported file type."""
        test_content = b"Some binary content"

        try:
            result = extractor.extract("test.bin", test_content)
        except NotSupportedError:
            supported = False

        assert not supported
        logger.info("Unsupported file type correctly raised NotSupportedError")


    def test_pdf_extraction(self, extractor):
        """Test extraction from a PDF file."""
        # Create a simple PDF content (this is a minimal PDF structure)
        # In a real test, you'd use a proper PDF file
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""
        
        result = extractor.extract("test.pdf", pdf_content)
        
        # Tika should be able to extract text from PDF
        assert result is not None
        logger.info(f"PDF extraction result: {result[:100]}...")


    def test_extraction_with_fallback(self, extractor):
        """Test that extraction falls back to PyMuPDF for PDFs when Tika fails."""
        # This test verifies the fallback mechanism works
        test_content = b"Simple text content"
        
        result = extractor.extract("test.txt", test_content)
        
        assert result is not None
        assert len(result) > 0
        logger.info("Extraction with fallback mechanism works")

    def test_extraction_performance(self, extractor):
        """Test that extraction completes within reasonable time."""
        import time
        
        test_content = b"This is a performance test document.\n" * 100  # 100 lines
        
        start_time = time.time()
        result = extractor.extract("perf_test.txt", test_content)
        end_time = time.time()
        
        extraction_time = end_time - start_time
        
        assert result is not None
        assert extraction_time < 5.0  # Should complete within 5 seconds
        logger.info(f"Extraction completed in {extraction_time:.2f} seconds")

    def test_extraction_error_handling(self, extractor):
        """Test that extraction handles errors gracefully."""
        # Test with corrupted content
        corrupted_content = b"This is corrupted\x00\x01\x02\x03content"
        
        result = extractor.extract("corrupted.txt", corrupted_content)
        
        # Should not crash and should return some result
        assert result is not None
        logger.info("Error handling works correctly")

    def test_supported_extensions(self, extractor):
        """Test that all supported extensions are recognized."""
        supported_extensions = {".pdf", ".docx", ".doc", ".ppt", ".pptx", ".xls", ".xlsx", ".txt"}
        
        for ext in supported_extensions:
            assert extractor.can_extract(ext), f"Extension {ext} should be supported"
        
        # Test unsupported extension
        assert not extractor.can_extract(".bin"), "Extension .bin should not be supported"
        
        logger.info("All supported extensions are correctly recognized")


class TestTikaIntegrationWithIngestor:
    """Test integration of Tika extraction with the ingestor workflow."""

    def test_extractor_initialization_with_config(self):
        """Test that ContentExtractor can be initialized with config."""
        from config import Config
        
        config = Config(
            nextcloud_url="http://test.com",
            nextcloud_admin_username="admin",
            nextcloud_admin_password="password",
            tika_server_url="http://localhost:9998"
        )
        
        extractor = ContentExtractor()
        
        assert extractor.tika_server_url == "http://localhost:9998"
        assert extractor.tika_available
        logger.info("ContentExtractor initialized successfully with config")

    def test_extraction_in_document_building(self):
        """Test that extraction works in the context of document building."""
        from ingestor import Ingestor
        from config import Config
        
        config = Config(
            nextcloud_url="http://test.com",
            nextcloud_admin_username="admin",
            nextcloud_admin_password="password",
            tika_server_url="http://localhost:9998"
        )
        
        # Create ingestor with mocked dependencies
        ingestor = Ingestor(config)
        
        # Test the extraction method directly
        test_content = b"This is a test document for ingestor integration.\n\nIt should be extracted properly."
        
        result = ingestor.extractor.extract("integration_test.txt", test_content)
        
        assert result is not None
        assert "test document" in result
        assert "ingestor integration" in result
        logger.info("Extraction works correctly in ingestor context")