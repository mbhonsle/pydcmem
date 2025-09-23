"""
Unit tests for UserAttributeClient class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pydc_mem.core.memory_client import UserAttributeClient, UpsertReport, UpsertItemResult
from pydc_mem.core.memory_extractor import MemoryCandidate


class TestUpsertItemResult:
    """Test UpsertItemResult dataclass."""
    
    def test_upsert_item_result_creation(self):
        """Test creating UpsertItemResult."""
        result = UpsertItemResult(
            attribute="test_attr",
            old_value="old_value",
            new_value="new_value",
            action="updated",
            status_code=200
        )
        assert result.attribute == "test_attr"
        assert result.old_value == "old_value"
        assert result.new_value == "new_value"
        assert result.action == "updated"
        assert result.status_code == 200
        assert result.error is None


class TestUpsertReport:
    """Test UpsertReport dataclass."""
    
    def test_upsert_report_creation(self):
        """Test creating UpsertReport."""
        report = UpsertReport(user_id="user123")
        assert report.user_id == "user123"
        assert report.added == 0
        assert report.updated == 0
        assert report.skipped == 0
        assert report.errors == 0
        assert report.details == []
    
    def test_upsert_report_str(self):
        """Test UpsertReport string representation."""
        report = UpsertReport(user_id="user123", added=2, updated=1, skipped=0, errors=0)
        expected = "UpsertReport(user_id=user123, added=2, updated=1, skipped=0, errors=0)"
        assert str(report) == expected


class TestUserAttributeClient:
    """Test UserAttributeClient functionality."""
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_init(self, mock_query_client, mock_ingestion_client):
        """Test UserAttributeClient initialization."""
        client = UserAttributeClient()
        
        assert client.dlo == "test_dlo"
        assert client.connector == "test_connector"
        assert client.vector_index_dlm == "test_vector_index"
        assert client.chunk_dlm == "test_chunk_dlm"
        assert client.tenantId == "test_org_id"
        assert client.query_svc_client == mock_query_client.return_value
        assert client.ingestion_client == mock_ingestion_client.return_value
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_fetch_relevant_attributes_success(self, mock_query_client, mock_ingestion_client, mock_httpx_response):
        """Test successful fetch of relevant attributes."""
        mock_query_client.return_value.read_data.return_value = mock_httpx_response
        
        client = UserAttributeClient()
        result = client.fetch_relevant_attributes("user123", "I prefer Delta")
        
        assert len(result) == 2
        assert result[0]["attr1"] == "attr1"
        assert result[0]["value1"] == "value1"
        assert result[0]["user1"] == "user1"
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_fetch_relevant_attributes_no_response(self, mock_query_client, mock_ingestion_client):
        """Test fetch relevant attributes with no response."""
        mock_query_client.return_value.read_data.return_value = None
        
        client = UserAttributeClient()
        result = client.fetch_relevant_attributes("user123", "I prefer Delta")
        
        assert result == []
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_fetch_relevant_attributes_parse_error(self, mock_query_client, mock_ingestion_client):
        """Test fetch relevant attributes with parse error."""
        mock_response = Mock()
        mock_response.json.side_effect = Exception("Parse error")
        mock_query_client.return_value.read_data.return_value = mock_response
        
        client = UserAttributeClient()
        result = client.fetch_relevant_attributes("user123", "I prefer Delta")
        
        assert result == []
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_fetch_user_attributes_success(self, mock_query_client, mock_ingestion_client, mock_httpx_response):
        """Test successful fetch of user attributes."""
        mock_query_client.return_value.read_data.return_value = mock_httpx_response
        
        client = UserAttributeClient()
        result = client.fetch_user_attributes("user123")
        
        assert len(result) == 2
        assert result[0]["attr1"] == "attr1"
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_upsert_from_candidates_new_attributes(self, mock_query_client, mock_ingestion_client, sample_memory_candidates):
        """Test upsert with new attributes."""
        # Mock empty current attributes
        mock_query_client.return_value.read_data.return_value = Mock()
        mock_query_client.return_value.read_data.return_value.json.return_value = {
            "data": [],
            "metadata": {}
        }
        
        # Mock successful creation
        mock_ingestion_client.return_value.ingest_data.return_value = Mock()
        mock_ingestion_client.return_value.ingest_data.return_value.status_code = 200
        
        client = UserAttributeClient()
        report = client.upsert_from_candidates("user123", sample_memory_candidates)
        
        assert report.user_id == "user123"
        assert report.added == 3  # All 3 candidates are new
        assert report.updated == 0
        assert report.skipped == 0
        assert report.errors == 0
        assert len(report.details) == 3
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_upsert_from_candidates_existing_attributes(self, mock_query_client, mock_ingestion_client, sample_memory_candidates, sample_user_attributes):
        """Test upsert with existing attributes."""
        # Mock existing attributes - need to mock the parsed format that fetch_user_attributes returns
        mock_query_client.return_value.read_data.return_value = Mock()
        mock_query_client.return_value.read_data.return_value.json.return_value = {
            "data": [
                ["attr1", "preferred_airline", "Delta Airlines", "user123"],
                ["attr2", "seat_preference", "aisle", "user123"]  # Different value
            ],
            "metadata": {
                "id__c": {"placeInOrder": 0, "type": "VARCHAR"},
                "attribute__c": {"placeInOrder": 1, "type": "VARCHAR"},
                "value__c": {"placeInOrder": 2, "type": "VARCHAR"},
                "userId__c": {"placeInOrder": 3, "type": "VARCHAR"}
            }
        }
        
        # Mock successful update
        mock_ingestion_client.return_value.ingest_data.return_value = Mock()
        mock_ingestion_client.return_value.ingest_data.return_value.status_code = 200
        
        client = UserAttributeClient()
        report = client.upsert_from_candidates("user123", sample_memory_candidates)
        
        assert report.user_id == "user123"
        assert report.added == 1  # meal_preference is new
        assert report.updated == 1  # seat_preference changed from aisle to window
        assert report.skipped == 1  # preferred_airline unchanged
        assert report.errors == 0
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_upsert_from_candidates_with_errors(self, mock_query_client, mock_ingestion_client, sample_memory_candidates):
        """Test upsert with creation errors."""
        # Mock empty current attributes
        mock_query_client.return_value.read_data.return_value = Mock()
        mock_query_client.return_value.read_data.return_value.json.return_value = {
            "data": [],
            "metadata": {}
        }
        
        # Mock creation error
        mock_ingestion_client.return_value.ingest_data.return_value = Mock()
        mock_ingestion_client.return_value.ingest_data.return_value.status_code = 400
        
        client = UserAttributeClient()
        report = client.upsert_from_candidates("user123", sample_memory_candidates)
        
        assert report.errors == 3  # All 3 failed
        assert report.added == 0
        assert len(report.details) == 3
        for detail in report.details:
            assert detail.status_code == 400

    def test_norm(self):
        """Test _norm static method."""
        assert UserAttributeClient._norm("Preferred Airline") == "preferred_airline"
        assert UserAttributeClient._norm("  SEAT PREFERENCE  ") == "seat_preference"
        assert UserAttributeClient._norm("meal-preference") == "meal-preference"
    
    def test_equal(self):
        """Test _equal static method."""
        # Case insensitive
        assert UserAttributeClient._equal("Delta", "DELTA", True) == True
        assert UserAttributeClient._equal("  Delta  ", "DELTA", True) == True
        assert UserAttributeClient._equal("Delta", "United", True) == False
        
        # Case sensitive
        assert UserAttributeClient._equal("Delta", "Delta", False) == True
        assert UserAttributeClient._equal("Delta", "DELTA", False) == False
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_create_attribute(self, mock_query_client, mock_ingestion_client):
        """Test _create_attribute method."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_ingestion_client.return_value.ingest_data.return_value = mock_response
        
        client = UserAttributeClient()
        status, error = client._create_attribute("user123", "test_attr", "test_value")
        
        assert status == 201
        assert error is None
        mock_ingestion_client.return_value.ingest_data.assert_called_once()
    
    @patch('pydc_mem.core.memory_client.DataCloudIngestionClient')
    @patch('pydc_mem.core.memory_client.QueryServiceClient')
    def test_update_attribute(self, mock_query_client, mock_ingestion_client):
        """Test _update_attribute method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_ingestion_client.return_value.ingest_data.return_value = mock_response
        
        client = UserAttributeClient()
        update_obj = {
            "id": "attr123",
            "value__c": "new_value",
            "lastModifiedAt__c": "2024-01-01 12:00:00"
        }
        status, error = client._update_attribute(update_obj)
        
        assert status == 200
        assert error is None
        mock_ingestion_client.return_value.ingest_data.assert_called_once()
    
    def test_status_err_success(self):
        """Test _status_err with successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        status, error = UserAttributeClient._status_err(mock_response)
        assert status == 200
        assert error is None
    
    def test_status_err_error(self):
        """Test _status_err with error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}
        
        status, error = UserAttributeClient._status_err(mock_response)
        assert status == 400
        assert error == "Bad request"
    
    def test_status_err_no_response(self):
        """Test _status_err with no response."""
        status, error = UserAttributeClient._status_err(None)
        assert status is None
        assert error == "request failed (no response)"
