"""
Tests for activity filtering in the Ingestor class.

This module tests the client-side filtering logic that ensures only newer
activity_ids are processed than the latest one saved in the state manager.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from nextcloud_ingestor.src.ingestor import Ingestor
from nextcloud_ingestor.src.config import Config
from nextcloud_ingestor.src.state_manager import StateManager


class TestIngestorActivityFiltering:
    """Test cases for activity filtering in incremental ingest."""

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
            postgres_password="test_password"
        )

    @pytest.fixture
    def mock_activities_response_with_old_ids(self):
        """Mock response with some activities having IDs <= last_processed_id."""
        return {
            "ocs": {
                "data": [
                    {
                        "activity_id": 100,  # This should be filtered out (<= 100)
                        "type": "file_created",
                        "app": "files",
                        "object_type": "files",
                        "object_name": "/user1/dossiers/dossier1/file1.txt",
                        "subject": "You created file1.txt"
                    },
                    {
                        "activity_id": 101,  # This should be kept (> 100)
                        "type": "file_created",
                        "app": "files",
                        "object_type": "files",
                        "object_name": "/user1/dossiers/dossier1/file2.txt",
                        "subject": "You created file2.txt"
                    },
                    {
                        "activity_id": 99,   # This should be filtered out (< 100)
                        "type": "file_changed",
                        "app": "files",
                        "object_type": "files",
                        "object_name": "/user1/dossiers/dossier1/file3.txt",
                        "subject": "You changed file3.txt"
                    },
                    {
                        "activity_id": 102,  # This should be kept (> 100)
                        "type": "file_deleted",
                        "app": "files",
                        "object_type": "files",
                        "object_name": "/user1/dossiers/dossier1/file4.txt",
                        "subject": "You deleted file4.txt"
                    }
                ]
            }
        }

    @pytest.fixture
    def mock_activities_response_all_new(self):
        """Mock response with all activities having IDs > last_processed_id."""
        return {
            "ocs": {
                "data": [
                    {
                        "activity_id": 101,
                        "type": "file_created",
                        "app": "files",
                        "object_type": "files",
                        "object_name": "/user1/dossiers/dossier1/file1.txt",
                        "subject": "You created file1.txt"
                    },
                    {
                        "activity_id": 102,
                        "type": "file_changed",
                        "app": "files",
                        "object_type": "files",
                        "object_name": "/user1/dossiers/dossier1/file2.txt",
                        "subject": "You changed file2.txt"
                    }
                ]
            }
        }

    @pytest.fixture
    def mock_activities_response_all_old(self):
        """Mock response with all activities having IDs <= last_processed_id."""
        return {
            "ocs": {
                "data": [
                    {
                        "activity_id": 100,  # This should be filtered out (= 100)
                        "type": "file_created",
                        "app": "files",
                        "object_type": "files",
                        "object_name": "/user1/dossiers/dossier1/file1.txt",
                        "subject": "You created file1.txt"
                    },
                    {
                        "activity_id": 99,   # This should be filtered out (< 100)
                        "type": "file_changed",
                        "app": "files",
                        "object_type": "files",
                        "object_name": "/user1/dossiers/dossier1/file2.txt",
                        "subject": "You changed file2.txt"
                    }
                ]
            }
        }

    @pytest.mark.asyncio
    async def test_activity_filtering_mixed_ids(self, mock_config, mock_activities_response_with_old_ids):
        """Test filtering when some activities have IDs <= last_processed_id."""
        last_activity_id = 100
        
        # Mock the dependencies
        with patch('ingestor.NextCloudConnector') as mock_nc_class, \
             patch('ingestor.ESClient') as mock_es_class, \
             patch('ingestor.ContentExtractor') as mock_extractor_class, \
             patch('ingestor.StateManager') as mock_state_class:
            
            # Setup mocks
            mock_nc = AsyncMock()
            mock_nc.get_activities_since.return_value = mock_activities_response_with_old_ids
            mock_nc.filter_file_activities.return_value = mock_activities_response_with_old_ids["ocs"]["data"]
            mock_nc.extract_file_paths_from_activities.return_value = {
                "created": {"/user1/dossiers/dossier1/file1.txt", "/user1/dossiers/dossier1/file2.txt"},
                "updated": {"/user1/dossiers/dossier1/file3.txt"},
                "deleted": {"/user1/dossiers/dossier1/file4.txt"}
            }
            mock_nc_class.return_value = mock_nc
            
            mock_es = MagicMock()
            mock_es.dry_run = False
            mock_es.recreate_indices.return_value = None
            mock_es.do_index_documents.return_value = None
            mock_es.delete_documents_by_path.return_value = None
            mock_es.get_document_info.return_value = None
            mock_es.document_exists.return_value = False
            mock_es.update_dossier_stats.return_value = None
            mock_es_class.return_value = mock_es
            
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = "test content"
            mock_extractor_class.return_value = mock_extractor
            
            mock_state = MagicMock()
            mock_state.get_last_activity_state.return_value = (last_activity_id, "2024-01-01T00:00:00Z")
            mock_state.update_activity_state.return_value = None
            mock_state.initialize_schema.return_value = None
            mock_state.close.return_value = None
            mock_state_class.return_value = mock_state
            
            # Create ingestor and run incremental ingest
            ingestor = Ingestor(mock_config)
            ingestor.nc = mock_nc
            ingestor.es = mock_es
            ingestor.extractor = mock_extractor
            ingestor.state_manager = mock_state
            
            # Run the incremental ingest
            await ingestor.run_incremental_ingest(dry_run=True, fallback_to_full=False)
            
            # Verify that get_activities_since was called with the correct last_activity_id
            mock_nc.get_activities_since.assert_called_once_with(last_activity_id)
            
            # Verify that filter_file_activities was called with only the newer activities
            # (activities with IDs > 100: [101, 102])
            filtered_activities = mock_nc.filter_file_activities.call_args[0][0]
            filtered_ids = [a["activity_id"] for a in filtered_activities]
            assert 101 in filtered_ids
            assert 102 in filtered_ids
            assert 100 not in filtered_ids  # Should be filtered out
            assert 99 not in filtered_ids   # Should be filtered out
            
            # Verify that update_activity_state was called with the highest activity ID
            mock_state.update_activity_state.assert_called_with(102)  # Highest ID from newer activities

    @pytest.mark.asyncio
    async def test_activity_filtering_all_new_ids(self, mock_config, mock_activities_response_all_new):
        """Test filtering when all activities have IDs > last_processed_id."""
        last_activity_id = 100
        
        # Mock the dependencies
        with patch('ingestor.NextCloudConnector') as mock_nc_class, \
             patch('ingestor.ESClient') as mock_es_class, \
             patch('ingestor.ContentExtractor') as mock_extractor_class, \
             patch('ingestor.StateManager') as mock_state_class:
            
            # Setup mocks
            mock_nc = AsyncMock()
            mock_nc.get_activities_since.return_value = mock_activities_response_all_new
            mock_nc.filter_file_activities.return_value = mock_activities_response_all_new["ocs"]["data"]
            mock_nc.extract_file_paths_from_activities.return_value = {
                "created": {"/user1/dossiers/dossier1/file1.txt"},
                "updated": {"/user1/dossiers/dossier1/file2.txt"},
                "deleted": set()
            }
            mock_nc_class.return_value = mock_nc
            
            mock_es = MagicMock()
            mock_es.dry_run = False
            mock_es.recreate_indices.return_value = None
            mock_es.do_index_documents.return_value = None
            mock_es.delete_documents_by_path.return_value = None
            mock_es.get_document_info.return_value = None
            mock_es.document_exists.return_value = False
            mock_es.update_dossier_stats.return_value = None
            mock_es_class.return_value = mock_es
            
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = "test content"
            mock_extractor_class.return_value = mock_extractor
            
            mock_state = MagicMock()
            mock_state.get_last_activity_state.return_value = (last_activity_id, "2024-01-01T00:00:00Z")
            mock_state.update_activity_state.return_value = None
            mock_state.initialize_schema.return_value = None
            mock_state.close.return_value = None
            mock_state_class.return_value = mock_state
            
            # Create ingestor and run incremental ingest
            ingestor = Ingestor(mock_config)
            ingestor.nc = mock_nc
            ingestor.es = mock_es
            ingestor.extractor = mock_extractor
            ingestor.state_manager = mock_state
            
            # Run the incremental ingest
            await ingestor.run_incremental_ingest(dry_run=True, fallback_to_full=False)
            
            # Verify that filter_file_activities was called with all activities
            # (since all have IDs > 100)
            filtered_activities = mock_nc.filter_file_activities.call_args[0][0]
            assert len(filtered_activities) == 2
            filtered_ids = [a["activity_id"] for a in filtered_activities]
            assert 101 in filtered_ids
            assert 102 in filtered_ids
            
            # Verify that update_activity_state was called with the highest activity ID
            mock_state.update_activity_state.assert_called_with(102)

    @pytest.mark.asyncio
    async def test_activity_filtering_all_old_ids(self, mock_config, mock_activities_response_all_old):
        """Test filtering when all activities have IDs <= last_processed_id."""
        last_activity_id = 100
        
        # Mock the dependencies
        with patch('ingestor.NextCloudConnector') as mock_nc_class, \
             patch('ingestor.ESClient') as mock_es_class, \
             patch('ingestor.ContentExtractor') as mock_extractor_class, \
             patch('ingestor.StateManager') as mock_state_class:
            
            # Setup mocks
            mock_nc = AsyncMock()
            mock_nc.get_activities_since.return_value = mock_activities_response_all_old
            mock_nc_class.return_value = mock_nc
            
            mock_es = MagicMock()
            mock_es.dry_run = False
            mock_es.recreate_indices.return_value = None
            mock_es_class.return_value = mock_es
            
            mock_extractor = MagicMock()
            mock_extractor_class.return_value = mock_extractor
            
            mock_state = MagicMock()
            mock_state.get_last_activity_state.return_value = (last_activity_id, "2024-01-01T00:00:00Z")
            mock_state.update_activity_state.return_value = None
            mock_state.initialize_schema.return_value = None
            mock_state.close.return_value = None
            mock_state_class.return_value = mock_state
            
            # Create ingestor and run incremental ingest
            ingestor = Ingestor(mock_config)
            ingestor.nc = mock_nc
            ingestor.es = mock_es
            ingestor.extractor = mock_extractor
            ingestor.state_manager = mock_state
            
            # Run the incremental ingest
            await ingestor.run_incremental_ingest(dry_run=True, fallback_to_full=False)
            
            # Verify that filter_file_activities was NOT called (no newer activities)
            mock_nc.filter_file_activities.assert_not_called()
            
            # Verify that update_activity_state was called with the highest activity ID from all activities
            mock_state.update_activity_state.assert_called_with(100)  # Highest ID from all activities

    @pytest.mark.asyncio
    async def test_activity_filtering_empty_response(self, mock_config):
        """Test filtering when no activities are returned."""
        last_activity_id = 100
        empty_response = {"ocs": {"data": []}}
        
        # Mock the dependencies
        with patch('ingestor.NextCloudConnector') as mock_nc_class, \
             patch('ingestor.ESClient') as mock_es_class, \
             patch('ingestor.ContentExtractor') as mock_extractor_class, \
             patch('ingestor.StateManager') as mock_state_class:
            
            # Setup mocks
            mock_nc = AsyncMock()
            mock_nc.get_activities_since.return_value = empty_response
            mock_nc_class.return_value = mock_nc
            
            mock_es = MagicMock()
            mock_es.dry_run = False
            mock_es.recreate_indices.return_value = None
            mock_es_class.return_value = mock_es
            
            mock_extractor = MagicMock()
            mock_extractor_class.return_value = mock_extractor
            
            mock_state = MagicMock()
            mock_state.get_last_activity_state.return_value = (last_activity_id, "2024-01-01T00:00:00Z")
            mock_state.update_activity_state.return_value = None
            mock_state.initialize_schema.return_value = None
            mock_state.close.return_value = None
            mock_state_class.return_value = mock_state
            
            # Create ingestor and run incremental ingest
            ingestor = Ingestor(mock_config)
            ingestor.nc = mock_nc
            ingestor.es = mock_es
            ingestor.extractor = mock_extractor
            ingestor.state_manager = mock_state
            
            # Run the incremental ingest
            await ingestor.run_incremental_ingest(dry_run=True, fallback_to_full=False)
            
            # Verify that filter_file_activities was NOT called (no activities)
            mock_nc.filter_file_activities.assert_not_called()
            
            # Verify that update_activity_state was NOT called (no activities to update)
            mock_state.update_activity_state.assert_not_called()