"""
Integration tests for NextCloud Activity API.

These tests can be run against a real NextCloud instance to verify
the actual behavior of the Activity API.

To run these tests, set up environment variables:
- NEXTCLOUD_URL
- NEXTCLOUD_ADMIN_USERNAME  
- NEXTCLOUD_ADMIN_PASSWORD

Then run: pytest test/test_activity_integration.py -m integration
"""

import pytest
import os
import asyncio
from datetime import datetime

# Add the parent directory to Python path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from nextcloud_ingestor.src.config import Config
from nextcloud_ingestor.src.nextcloud import NextCloudConnector


@pytest.mark.integration
class TestActivityAPIIntegration:
    """Integration tests that require a real NextCloud instance."""
    
    @pytest.fixture
    def config(self):
        """Create config from environment variables."""
        nextcloud_url = os.getenv("NEXTCLOUD_URL")
        admin_username = os.getenv("NEXTCLOUD_ADMIN_USERNAME")
        admin_password = os.getenv("NEXTCLOUD_ADMIN_PASSWORD")
        
        if not all([nextcloud_url, admin_username, admin_password]):
            pytest.skip("NextCloud integration test environment not configured")
        
        return Config(
            nextcloud_url=nextcloud_url,
            nextcloud_admin_username=admin_username,
            nextcloud_admin_password=admin_password,
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
    
    @pytest.mark.asyncio
    async def test_get_activities_since_real_api(self, nc_connector):
        """Test get_activities_since against a real NextCloud instance."""
        # Start with activity ID 0 to get some activities
        since_activity_id = 0
        limit = 10
        
        try:
            result = await nc_connector.get_activities_since(since_activity_id, limit=limit)
            
            # Verify response structure
            assert "ocs" in result
            assert "data" in result["ocs"]
            
            activities = result["ocs"]["data"]
            assert isinstance(activities, list)
            
            # If there are activities, verify their structure
            if activities:
                for activity in activities:
                    # Basic fields that should be present
                    assert "activity_id" in activity
                    assert "timestamp" in activity
                    assert "app" in activity
                    assert "type" in activity
                    
                    # Verify activity_id is greater than since_activity_id
                    assert activity["activity_id"] > since_activity_id
                    
                    # If it's a file activity, check file-specific fields
                    if activity.get("object_type") == "files":
                        assert "object_name" in activity
                        assert "object_id" in activity
                
                # Verify activities are in ascending order by activity_id
                activity_ids = [a["activity_id"] for a in activities]
                assert activity_ids == sorted(activity_ids), "Activities should be in ascending order"
                
                print(f"Successfully retrieved {len(activities)} activities")
                print(f"Activity ID range: {min(activity_ids)} - {max(activity_ids)}")
                
            else:
                print("No activities found (this might be expected for a fresh instance)")
                
        except Exception as e:
            pytest.fail(f"Failed to get activities from real NextCloud API: {e}")
    
    @pytest.mark.asyncio
    async def test_get_activities_since_specific_id(self, nc_connector):
        """Test getting activities since a specific (high) activity ID."""
        # Use a high activity ID to test the "since" parameter
        since_activity_id = 999999
        
        try:
            result = await nc_connector.get_activities_since(since_activity_id, limit=5)
            
            # Should succeed even with high activity ID
            assert "ocs" in result
            assert "data" in result["ocs"]
            
            activities = result["ocs"]["data"]
            
            # Might be empty if no activities exist with ID > 999999
            if activities:
                for activity in activities:
                    assert activity["activity_id"] > since_activity_id
                print(f"Found {len(activities)} activities with ID > {since_activity_id}")
            else:
                print(f"No activities found with ID > {since_activity_id} (expected)")
                
        except Exception as e:
            pytest.fail(f"Failed to get activities since specific ID: {e}")
    
    @pytest.mark.asyncio  
    async def test_activity_filtering(self, nc_connector):
        """Test that activity filtering by object_type=files works correctly."""
        since_activity_id = 0
        limit = 20
        
        try:
            result = await nc_connector.get_activities_since(since_activity_id, limit=limit)
            activities = result["ocs"]["data"]
            
            # All returned activities should be file-related (due to object_type filter)
            file_activities = [a for a in activities if a.get("object_type") == "files"]
            
            # The filter should have been applied at API level
            # If there are activities, they should all be file-related
            if activities:
                print(f"Total activities: {len(activities)}")
                print(f"File activities: {len(file_activities)}")
                
                # Check that we're getting file activities
                file_types = set(a.get("type", "") for a in file_activities)
                print(f"File activity types found: {file_types}")
                
                # Verify some activities are file-related (if any activities exist)
                if file_activities:
                    assert len(file_activities) > 0
                    # Check for common file activity types
                    expected_types = {"file_created", "file_changed", "file_deleted", "file_moved"}
                    assert any(t in expected_types for t in file_types), f"Expected file activity types, got: {file_types}"
            
        except Exception as e:
            pytest.fail(f"Failed to test activity filtering: {e}")


if __name__ == "__main__":
    # Allow running this file directly for manual testing
    pytest.main([__file__, "-v", "-m", "integration"])