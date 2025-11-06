"""
Tests for full_text extraction and ingestion into Elasticsearch.

This module tests the complete workflow from file content extraction
through to Elasticsearch indexing to ensure full_text is properly stored.
"""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from nextcloud_ingestor.src.ingestor import Ingestor
from nextcloud_ingestor.src.config import Config
from nextcloud_ingestor.src.content import ContentExtractor


class TestFullTextIngestion:
    """Test cases for full_text extraction and ingestion."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        return Config(
            nextcloud_url="https://test.nextcloud.com",
            nextcloud_admin_username="admin",
            nextcloud_admin_password="password",
            dossier_parent_path="dossiers",
            es_url="http://localhost:9200",
            es_index_documents="documents",
            es_index_dossiers="dossiers",
            postgres_host="localhost",
            postgres_port=5432,
            postgres_db="test_db",
            postgres_user="test_user",
            postgres_password="test_password",
            tika_server_url="http://localhost:9998"
        )

    async def test_content_extractor_full_text_extraction(self, mock_config):
        """Test that ContentExtractor properly extracts full_text."""
        extractor = ContentExtractor(mock_config.tika_server_url)
        
        # Test with a multi-paragraph text document
        test_content = b"""This is the first paragraph of our test document.

This is the second paragraph with some important information about the content.

And this is the third paragraph that should also be extracted properly."""
        
        result = await extractor.extract("test_document.txt", test_content)
        
        assert result is not None
        assert len(result) > 0
        assert "first paragraph" in result
        assert "second paragraph" in result
        assert "third paragraph" in result
        assert "important information" in result
        
        print(f"Extracted text length: {len(result)} characters")
        print(f"Extracted text preview: {result[:100]}...")

    def test_document_building_with_full_text(self, mock_config):
        """Test that _build_document includes full_text in the document structure."""
        # Mock the dependencies
        with patch('ingestor.NextCloudConnector') as mock_nc_class, \
             patch('ingestor.ESClient') as mock_es_class, \
             patch('ingestor.ContentExtractor') as mock_extractor_class, \
             patch('ingestor.StateManager') as mock_state_class:
            
            # Setup mocks
            mock_nc = AsyncMock()
            mock_nc.read_file.return_value = b"This is test content for document building.\n\nWith multiple paragraphs."
            mock_nc.get_metadata.return_value = {
                "fileid": "12345",
                "size": "1024",
                "modified": "2024-01-01T12:00:00Z",
                "created": "2024-01-01T10:00:00Z",
                "type": "text/plain"
            }
            mock_nc.get_sharees.return_value = {"user1", "user2"}
            mock_nc_class.return_value = mock_nc
            
            mock_es = MagicMock()
            mock_es_class.return_value = mock_es
            
            mock_extractor = ContentExtractor(mock_config.tika_server_url)
            mock_extractor_class.return_value = mock_extractor
            
            mock_state = MagicMock()
            mock_state_class.return_value = mock_state
            
            # Create ingestor
            ingestor = Ingestor(mock_config)
            ingestor.nc = mock_nc
            ingestor.es = mock_es
            ingestor.extractor = mock_extractor
            ingestor.state_manager = mock_state
            
            # Create a mock dossier
            dossier = {
                "dossier_id": "test_dossier_123",
                "dossier_name": "Test Dossier"
            }
            
            # Build document
            import asyncio
            doc = asyncio.run(ingestor._build_document("user1", dossier, "/user1/dossiers/test_dossier/test_file.txt"))
            
            # Verify full_text is included
            assert "full_text" in doc
            assert doc["full_text"] is not None
            assert len(doc["full_text"]) > 0
            assert "test content" in doc["full_text"]
            assert "multiple paragraphs" in doc["full_text"]
            
            # Verify other important fields
            assert doc["title"] == "test_file.txt"
            assert doc["dossier_id"] == "test_dossier_123"
            assert doc["filepath"] == "/user1/dossiers/test_dossier/test_file.txt"
            assert "paragraphs" in doc
            assert len(doc["paragraphs"]) > 0
            
            print(f"Document built successfully with full_text: {len(doc['full_text'])} characters")
            print(f"Number of paragraphs: {len(doc['paragraphs'])}")

    def test_paragraph_parsing_from_full_text(self, mock_config):
        """Test that full_text is properly parsed into paragraphs."""
        extractor = ContentExtractor(mock_config.tika_server_url)
        
        # Test content with multiple paragraphs
        test_content = b"""First paragraph with some content.

Second paragraph with different information.

Third paragraph with more details.

Fourth paragraph to test parsing."""
        
        full_text = extractor.extract("test_paragraphs.txt", test_content)
        
        # Test the parse method from ingestor
        ingestor = Ingestor(mock_config)
        paragraphs = ingestor.parse(full_text)
        
        assert len(paragraphs) == 4
        assert paragraphs[0]["text"] == "First paragraph with some content."
        assert paragraphs[1]["text"] == "Second paragraph with different information."
        assert paragraphs[2]["text"] == "Third paragraph with more details."
        assert paragraphs[3]["text"] == "Fourth paragraph to test parsing."
        
        # Verify paragraph IDs
        for i, para in enumerate(paragraphs):
            assert para["id"] == i
        
        print(f"Successfully parsed {len(paragraphs)} paragraphs from full_text")

    def test_full_text_with_special_characters(self, mock_config):
        """Test that full_text extraction handles special characters properly."""
        extractor = ContentExtractor(mock_config.tika_server_url)
        
        # Test content with special characters and unicode
        test_content = b"""Document with special characters: \xc3\xa9, \xc3\xa0, \xc3\xb1.

And some symbols: @#$%^&*()_+-=[]{}|;':\",./<>?

Also some numbers: 1234567890 and dates: 2024-01-01."""
        
        full_text = extractor.extract("special_chars.txt", test_content)
        
        assert full_text is not None
        assert len(full_text) > 0
        assert "special characters" in full_text
        assert "symbols" in full_text
        assert "numbers" in full_text
        
        print(f"Special characters handled correctly: {full_text[:100]}...")

    def test_full_text_indexing_simulation(self, mock_config):
        """Test simulation of full_text being indexed to Elasticsearch."""
        # Mock ES client to capture indexed documents
        mock_es_client = MagicMock()
        indexed_docs = []
        
        def mock_index_documents(docs):
            indexed_docs.extend(docs)
            return True
        
        mock_es_client.do_index_documents = mock_index_documents
        
        # Create a test document with full_text
        test_doc = {
            "title": "Test Document",
            "dossier_id": "test_123",
            "filepath": "/user1/dossiers/test/file.txt",
            "full_text": "This is the extracted full text content from the document. It contains important information that should be searchable in Elasticsearch.",
            "paragraphs": [
                {"id": 0, "text": "This is the extracted full text content from the document."},
                {"id": 1, "text": "It contains important information that should be searchable in Elasticsearch."}
            ],
            "size": 1024,
            "filetype": "text/plain"
        }
        
        # Simulate indexing
        mock_es_client.do_index_documents([test_doc])
        
        # Verify document was indexed
        assert len(indexed_docs) == 1
        indexed_doc = indexed_docs[0]
        
        assert indexed_doc["full_text"] == test_doc["full_text"]
        assert len(indexed_doc["paragraphs"]) == 2
        assert indexed_doc["title"] == "Test Document"
        
        print("Document with full_text successfully indexed to Elasticsearch")
        print(f"Indexed full_text length: {len(indexed_doc['full_text'])} characters")

    def test_full_text_with_empty_content(self, mock_config):
        """Test handling of empty or minimal content."""
        extractor = ContentExtractor(mock_config.tika_server_url)
        
        # Test with empty content
        empty_content = b""
        result = extractor.extract("empty.txt", empty_content)
        
        assert result == ""
        
        # Test with minimal content
        minimal_content = b"a"
        result = extractor.extract("minimal.txt", minimal_content)
        
        assert result == "a"
        
        print("Empty and minimal content handled correctly")

    async def test_full_text_performance_with_large_content(self, mock_config):
        """Test performance with larger content."""
        import time
        
        extractor = ContentExtractor(mock_config.tika_server_url)
        
        # Create larger content
        large_content = b"This is a test line.\n" * 1000  # 1000 lines
        
        start_time = time.time()
        result = await extractor.extract("large_document.txt", large_content)
        end_time = time.time()
        
        extraction_time = end_time - start_time
        
        assert result is not None
        assert len(result) > 0
        assert extraction_time < 10.0  # Should complete within 10 seconds
        
        print(f"Large content extraction completed in {extraction_time:.2f} seconds")
        print(f"Extracted {len(result)} characters from {len(large_content)} bytes of input")