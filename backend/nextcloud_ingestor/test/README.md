# Tests for NextCloud Ingestor

This directory contains tests for the NextCloud ingestor, particularly focusing on the Activity API integration.

## Test Structure

- `test_activity_api.py` - Unit tests for the `get_activities_since` method using mocks
- `test_activity_integration.py` - Integration tests that can run against a real NextCloud instance  
- `__init__.py` - Test package initialization

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements-test.txt
# or
make test-install
```

### Unit Tests

Run the Activity API unit tests:
```bash
python -m pytest test/test_activity_api.py -v
# or
make test-activity
```

Run all unit tests:
```bash
python -m pytest test/ -v
# or  
make test
```

### Integration Tests

Integration tests require a running NextCloud instance. Set up environment variables:

```bash
export NEXTCLOUD_URL=http://localhost:8080
export NEXTCLOUD_ADMIN_USERNAME=admin
export NEXTCLOUD_ADMIN_PASSWORD=admin_password
```

Then run:
```bash
python -m pytest test/test_activity_integration.py -m integration -v
```

Or use the development environment:
```bash
make run  # Start NextCloud, Postgres, and Elasticsearch
# Wait for services to start...
export NEXTCLOUD_URL=http://localhost:8080
export NEXTCLOUD_ADMIN_USERNAME=admin  
export NEXTCLOUD_ADMIN_PASSWORD=admin_password
python -m pytest test/test_activity_integration.py -m integration -v
```

## Test Coverage

The unit tests (`test_activity_api.py`) cover:

### Core Functionality
- ✅ Successful retrieval of activities since a specific ID
- ✅ Verification that returned activities have IDs greater than `since_activity_id`
- ✅ Activities returned in ascending order by ID
- ✅ Correct API parameters (since, limit, sort, object_type)
- ✅ Proper authentication headers

### Edge Cases  
- ✅ Empty response (HTTP 204)
- ✅ Not Modified response (HTTP 304)
- ✅ Custom limit parameter
- ✅ Request headers validation

### Error Handling
- ✅ Retry mechanism on server errors (5xx)
- ✅ No retry on client errors (4xx) 
- ✅ Network error handling
- ✅ Exhausted retry attempts
- ✅ Exponential backoff delay

### Data Validation
- ✅ Activity ID filtering logic
- ✅ Response structure validation
- ✅ Edge cases for activity ID boundaries

## Key Test Scenarios

### 1. Activity ID Filtering
The tests verify that:
- Only activities with `activity_id > since_activity_id` are returned
- The `since` parameter is correctly passed to the API
- Edge cases like `since_activity_id` equal to an existing ID work correctly

### 2. Request Parameters
Tests ensure the correct API call is made with:
- URL: `{nextcloud_url}/ocs/v2.php/apps/activity/api/v2/activity`
- Parameters: `since`, `limit`, `sort=asc`, `object_type=files`
- Headers: `OCS-APIRequest=true`, `Accept=application/json`
- Authentication: Basic auth with admin credentials

### 3. Error Resilience
Tests verify robust error handling:
- Server errors (5xx) trigger retries with exponential backoff
- Client errors (4xx) fail immediately without retries
- Network errors are handled gracefully
- All retries exhausted results in proper exception

### 4. Response Processing
Tests validate:
- Successful responses (200) are parsed correctly
- Empty responses (204, 304) return expected empty structure
- Response data structure matches expected format

## Mock Strategy

The unit tests use `unittest.mock` and `pytest-mock` to:
- Mock HTTP calls to avoid external dependencies
- Test different response scenarios (success, error, empty)
- Verify exact parameters passed to HTTP client
- Simulate network conditions and error states

## Integration Test Benefits

While unit tests provide comprehensive coverage, integration tests verify:
- Real API compatibility and response format
- Actual NextCloud behavior under different conditions
- End-to-end functionality with live data
- API changes or updates that might break compatibility

Run both unit and integration tests for complete confidence in the Activity API implementation.