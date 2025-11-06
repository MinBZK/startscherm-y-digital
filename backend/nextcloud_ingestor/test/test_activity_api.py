"""
Tests for NextCloud Activity API integration.

This module tests the get_activities_since function to ensure it correctly
retrieves activities from NextCloud since a specific activity ID.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# Add the parent directory to Python path to import our modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from nextcloud_ingestor.src.config import Config
from nextcloud_ingestor.src.nextcloud import NextCloudConnector


class TestGetActivitiesSince:
    """Test cases for the get_activities_since method."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return Config(
            nextcloud_url="http://test-nextcloud.com",
            nextcloud_admin_username="test_admin",
            nextcloud_admin_password="test_password",
            dossier_parent_path="dossiers",
            es_url="http://localhost:9200",
            es_index_documents="test-docs",
            es_index_dossiers="test-dossiers",
            postgres_host="localhost",
            postgres_port=5432,
            postgres_db="test_db",
            postgres_user="test_user",
            postgres_password="test_pass"
        )
    
    @pytest.fixture
    def nc_connector(self, config):
        """Create a NextCloudConnector instance for testing."""
        return NextCloudConnector(config)
    
    @pytest.fixture
    def mock_activities_response(self):
        """Sample activities response from NextCloud API."""
        return {
            "ocs": {
                "meta": {
                    "status": "ok",
                    "statuscode": 200,
                    "message": "OK"
                },
                "data": [
                    {
                        "activity_id": 101,
                        "timestamp": 1695734400,  # 2023-09-26 12:00:00 UTC
                        "app": "files",
                        "type": "file_created",
                        "user": "testuser",
                        "affecteduser": "testuser",
                        "subject": "testuser created test_file.txt",
                        "subject_rich": {
                            "0": "testuser created {file1}",
                            "1": {
                                "file1": {
                                    "type": "file",
                                    "id": 123,
                                    "name": "test_file.txt",
                                    "path": "/testuser/dossiers/test_dossier/test_file.txt"
                                }
                            }
                        },
                        "object_type": "files",
                        "object_id": 123,
                        "object_name": "/testuser/dossiers/test_dossier/test_file.txt"
                    },
                    {
                        "activity_id": 102,
                        "timestamp": 1695734460,  # 2023-09-26 12:01:00 UTC
                        "app": "files",
                        "type": "file_changed",
                        "user": "testuser",
                        "affecteduser": "testuser",
                        "subject": "testuser changed test_file.txt",
                        "object_type": "files",
                        "object_id": 123,
                        "object_name": "/testuser/dossiers/test_dossier/test_file.txt"
                    },
                    {
                        "activity_id": 103,
                        "timestamp": 1695734520,  # 2023-09-26 12:02:00 UTC
                        "app": "files",
                        "type": "file_deleted",
                        "user": "testuser",
                        "affecteduser": "testuser",
                        "subject": "testuser deleted old_file.txt",
                        "object_type": "files",
                        "object_id": 124,
                        "object_name": "/testuser/dossiers/test_dossier/old_file.txt"
                    }
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_get_activities_since_success(self, nc_connector, mock_activities_response):
        """Test successful retrieval of activities since a specific ID."""
        since_activity_id = 100
        
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_activities_response
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Call the method under test
            result = await nc_connector.get_activities_since(since_activity_id)
            
            # Verify the request was made correctly
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            
            # Check URL
            expected_url = f"{nc_connector.config.nextcloud_url}/ocs/v2.php/apps/activity/api/v2/activity"
            assert call_args[0][0] == expected_url
            
            # Check parameters
            params = call_args[1]["params"]
            assert params["since"] == since_activity_id
            assert params["limit"] == 50  # default value
            assert params["sort"] == "asc"
            assert params["object_type"] == "files"
            
            # # Check authentication
            # auth = call_args[1]["auth"]
            # assert auth == (nc_connector.config.nextcloud_admin_username, 
            #               nc_connector.config.nextcloud_admin_password)
            
            # Verify the result
            assert result == mock_activities_response
            activities = result["ocs"]["data"]
            assert len(activities) == 3
            
            # Verify all returned activities have IDs greater than since_activity_id
            for activity in activities:
                assert activity["activity_id"] > since_activity_id
            
            # Verify activities are returned in ascending order
            activity_ids = [a["activity_id"] for a in activities]
            assert activity_ids == sorted(activity_ids)
    
    @pytest.mark.asyncio
    async def test_get_activities_since_empty_response(self, nc_connector):
        """Test handling of empty response (no new activities)."""
        since_activity_id = 200
        
        mock_response = MagicMock()
        mock_response.status_code = 204
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await nc_connector.get_activities_since(since_activity_id)
            
            # Should return empty data structure
            expected_result = {"ocs": {"data": []}}
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_activities_since_not_modified(self, nc_connector):
        """Test handling of 304 Not Modified response."""
        since_activity_id = 200
        
        mock_response = MagicMock()
        mock_response.status_code = 304
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await nc_connector.get_activities_since(since_activity_id)
            
            # Should return empty data structure
            expected_result = {"ocs": {"data": []}}
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_activities_since_with_custom_limit(self, nc_connector, mock_activities_response):
        """Test get_activities_since with custom limit parameter."""
        since_activity_id = 100
        custom_limit = 25
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_activities_response
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            await nc_connector.get_activities_since(since_activity_id, limit=custom_limit)
            
            # Verify the custom limit was used
            call_args = mock_client.get.call_args
            params = call_args[1]["params"]
            assert params["limit"] == custom_limit
    
    @pytest.mark.asyncio
    async def test_get_activities_since_retry_on_failure(self, nc_connector):
        """Test retry mechanism on HTTP failures."""
        since_activity_id = 100
        
        # Mock first call to fail, second to succeed
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"ocs": {"data": []}}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=[mock_response_fail, mock_response_success])
            mock_client_class.return_value = mock_client
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await nc_connector.get_activities_since(since_activity_id, retries=2)
                
                # Should have retried once
                assert mock_client.get.call_count == 2
                mock_sleep.assert_called_once()  # Should sleep before retry
                
                # Should return successful result
                assert result == {"ocs": {"data": []}}
    
    @pytest.mark.asyncio
    async def test_get_activities_since_client_error_no_retry(self, nc_connector):
        """Test that client errors (4xx) are not retried."""
        since_activity_id = 100
        
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                await nc_connector.get_activities_since(since_activity_id, retries=2)
            
            # Should fail immediately without retries for 4xx errors
            assert mock_client.get.call_count == 1
            assert "Client error from Activity API: 403" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_activities_since_exhausted_retries(self, nc_connector):
        """Test behavior when all retries are exhausted."""
        since_activity_id = 100
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(Exception) as exc_info:
                    await nc_connector.get_activities_since(since_activity_id, retries=2)
                
                # Should have tried 3 times (initial + 2 retries)
                assert mock_client.get.call_count == 3
                assert "Failed to get activities after 3 attempts" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_activities_since_network_error(self, nc_connector):
        """Test handling of network errors."""
        since_activity_id = 100
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            mock_client_class.return_value = mock_client
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(Exception) as exc_info:
                    await nc_connector.get_activities_since(since_activity_id, retries=1)
                
                # Should have tried 2 times (initial + 1 retry)
                assert mock_client.get.call_count == 2
                assert "Failed to get activities after 2 attempts" in str(exc_info.value)
    
    def test_activity_id_filtering_logic(self, mock_activities_response):
        """Test that the logic for filtering activities by ID works correctly."""
        activities = mock_activities_response["ocs"]["data"]
        since_activity_id = 101
        
        # Filter activities as the function should
        filtered_activities = [a for a in activities if a["activity_id"] > since_activity_id]
        
        # Should only include activities 102 and 103
        assert len(filtered_activities) == 2
        assert filtered_activities[0]["activity_id"] == 102
        assert filtered_activities[1]["activity_id"] == 103
        
        # Test edge case: since_activity_id equal to an existing ID
        since_activity_id = 102
        filtered_activities = [a for a in activities if a["activity_id"] > since_activity_id]
        assert len(filtered_activities) == 1
        assert filtered_activities[0]["activity_id"] == 103
    
    @pytest.mark.asyncio
    async def test_get_activities_since_request_headers(self, nc_connector, mock_activities_response):
        """Test that correct headers are sent with the request."""
        since_activity_id = 100
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_activities_response
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            await nc_connector.get_activities_since(since_activity_id)
            
            # Verify headers
            call_args = mock_client.get.call_args
            headers = call_args[1]["headers"]
            assert headers == nc_connector.api_headers
            assert "OCS-APIRequest" in headers
            assert headers["OCS-APIRequest"] == "true"
            assert "Accept" in headers
            assert headers["Accept"] == "application/json"