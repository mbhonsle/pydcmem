"""
Unit tests for utility classes.
"""

import pytest
from unittest.mock import Mock, patch
from pydc_mem.util.ingestion_client import DataCloudIngestionClient
from pydc_mem.util.query_svc import QueryServiceClient, QueryOutput
from pydc_mem.util.memory_results_parser import parse_tabular_payload, Column, _parse_input, _columns_from_metadata, _coerce_value


class TestDataCloudIngestionClient:
    """Test DataCloudIngestionClient functionality."""
    
    @patch('pydc_mem.util.ingestion_client.DataCloudTokenGenerator')
    def test_init(self, mock_token_generator):
        """Test DataCloudIngestionClient initialization."""
        client = DataCloudIngestionClient(timeout=60)
        
        assert client.timeout == 60
        assert client.token_generator == mock_token_generator.return_value
        assert client.auth_token_response is None
        assert client.client is not None
    
    @patch('pydc_mem.util.ingestion_client.DataCloudTokenGenerator')
    def test_ingest_data_success(self, mock_token_generator, mock_data_cloud_token):
        """Test successful data ingestion."""
        mock_token_generator.return_value.get_dc_token.return_value = mock_data_cloud_token
        
        with patch('httpx.Client') as mock_httpx:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.raise_for_status.return_value = None
            mock_httpx.return_value.post.return_value = mock_response
            
            client = DataCloudIngestionClient()
            data = {"test": "data"}
            result = client.ingest_data(data, "test_connector", "test_dlo")
            
            assert result == mock_response
            mock_httpx.return_value.post.assert_called_once()
    
    @patch('pydc_mem.util.ingestion_client.DataCloudTokenGenerator')
    def test_ingest_data_http_error(self, mock_token_generator, mock_data_cloud_token):
        """Test data ingestion with HTTP error."""
        mock_token_generator.return_value.get_dc_token.return_value = mock_data_cloud_token
        
        with patch('httpx.Client') as mock_httpx:
            import httpx
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_httpx.return_value.post.side_effect = httpx.HTTPStatusError(
                "400 Bad Request", request=Mock(), response=mock_response
            )
            
            client = DataCloudIngestionClient()
            data = {"test": "data"}
            
            with pytest.raises(httpx.HTTPStatusError):
                client.ingest_data(data, "test_connector", "test_dlo")
    
    @patch('pydc_mem.util.ingestion_client.DataCloudTokenGenerator')
    def test_ingest_data_network_error(self, mock_token_generator, mock_data_cloud_token):
        """Test data ingestion with network error."""
        mock_token_generator.return_value.get_dc_token.return_value = mock_data_cloud_token
        
        with patch('httpx.Client') as mock_httpx:
            import httpx
            mock_httpx.return_value.post.side_effect = httpx.RequestError("Network error")
            
            client = DataCloudIngestionClient()
            data = {"test": "data"}
            
            with pytest.raises(httpx.RequestError, match="Network error"):
                client.ingest_data(data, "test_connector", "test_dlo")
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with patch('pydc_mem.util.ingestion_client.DataCloudTokenGenerator'):
            with DataCloudIngestionClient() as client:
                assert client is not None
                # Client should be closed when exiting context


class TestQueryServiceClient:
    """Test QueryServiceClient functionality."""
    
    @patch('pydc_mem.util.query_svc.SalesforceTokenGenerator')
    def test_init(self, mock_token_generator):
        """Test QueryServiceClient initialization."""
        client = QueryServiceClient(timeout=60)
        
        assert client.timeout == 60
        assert client.token_generator == mock_token_generator.return_value
        assert client.auth_token_response is None
        assert client.client is not None
    
    @patch('pydc_mem.util.query_svc.SalesforceTokenGenerator')
    def test_read_data_success(self, mock_token_generator, mock_salesforce_token):
        """Test successful data reading."""
        mock_token_generator.return_value.get_sf_token.return_value = mock_salesforce_token
        
        with patch('httpx.Client') as mock_httpx:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_httpx.return_value.post.return_value = mock_response
            
            client = QueryServiceClient()
            data = {"sql": "SELECT * FROM test"}
            result = client.read_data(data)
            
            assert result == mock_response
            mock_httpx.return_value.post.assert_called_once()
    
    @patch('pydc_mem.util.query_svc.SalesforceTokenGenerator')
    def test_read_data_http_error(self, mock_token_generator, mock_salesforce_token):
        """Test data reading with HTTP error."""
        mock_token_generator.return_value.get_sf_token.return_value = mock_salesforce_token
        
        with patch('httpx.Client') as mock_httpx:
            import httpx
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_httpx.return_value.post.side_effect = httpx.HTTPStatusError(
                "400 Bad Request", request=Mock(), response=mock_response
            )
            
            client = QueryServiceClient()
            data = {"sql": "SELECT * FROM test"}
            
            with pytest.raises(httpx.HTTPStatusError):
                client.read_data(data)
    
    @patch('pydc_mem.util.query_svc.SalesforceTokenGenerator')
    def test_read_data_network_error(self, mock_token_generator, mock_salesforce_token):
        """Test data reading with network error."""
        mock_token_generator.return_value.get_sf_token.return_value = mock_salesforce_token
        
        with patch('httpx.Client') as mock_httpx:
            import httpx
            mock_httpx.return_value.post.side_effect = httpx.RequestError("Network error")
            
            client = QueryServiceClient()
            data = {"sql": "SELECT * FROM test"}
            
            with pytest.raises(httpx.RequestError, match="Network error"):
                client.read_data(data)


class TestQueryOutput:
    """Test QueryOutput model."""
    
    def test_query_output_creation(self):
        """Test creating QueryOutput."""
        output = QueryOutput(id="123", score=0.95, payload="test payload")
        
        assert output.id == "123"
        assert output.score == 0.95
        assert output.payload == "test payload"


class TestMemoryResultsParser:
    """Test memory results parser functionality."""
    
    def test_column_creation(self):
        """Test Column dataclass creation."""
        column = Column(name="test_col", order=1, type="VARCHAR")
        
        assert column.name == "test_col"
        assert column.order == 1
        assert column.type == "VARCHAR"
    
    def test_parse_input_dict(self):
        """Test _parse_input with dict input."""
        input_dict = {"key": "value"}
        result = _parse_input(input_dict)
        
        assert result == input_dict
    
    def test_parse_input_json_string(self):
        """Test _parse_input with JSON string."""
        json_str = '{"key": "value"}'
        result = _parse_input(json_str)
        
        assert result == {"key": "value"}
    
    def test_parse_input_python_literal(self):
        """Test _parse_input with Python literal string."""
        literal_str = "{'key': 'value', 'number': 42, 'boolean': True}"
        result = _parse_input(literal_str)
        
        assert result == {"key": "value", "number": 42, "boolean": True}
    
    def test_columns_from_metadata(self):
        """Test _columns_from_metadata function."""
        metadata = {
            "col1": {"placeInOrder": 2, "type": "VARCHAR"},
            "col2": {"placeInOrder": 0, "type": "INTEGER"},
            "col3": {"placeInOrder": 1, "type": "TIMESTAMP"}
        }
        
        columns = _columns_from_metadata(metadata)
        
        assert len(columns) == 3
        assert columns[0].name == "col2"  # order 0
        assert columns[0].type == "INTEGER"
        assert columns[1].name == "col3"  # order 1
        assert columns[1].type == "TIMESTAMP"
        assert columns[2].name == "col1"  # order 2
        assert columns[2].type == "VARCHAR"
    
    def test_coerce_value_timestamp(self):
        """Test _coerce_value with timestamp types."""
        # Test UTC timestamp format
        result = _coerce_value("2024-01-01 12:00:00.000 UTC", "TIMESTAMP WITH TIME ZONE")
        assert result == "2024-01-01T12:00:00Z"
        
        # Test ISO format
        result = _coerce_value("2024-01-01T12:00:00Z", "TIMESTAMP")
        assert result == "2024-01-01T12:00:00Z"
        
        # Test without timezone
        result = _coerce_value("2024-01-01T12:00:00", "TIMESTAMP")
        assert result == "2024-01-01T12:00:00Z"
    
    def test_coerce_value_numeric(self):
        """Test _coerce_value with numeric types."""
        # Test decimal
        result = _coerce_value("123.45", "DECIMAL")
        assert result == 123.45
        
        # Test integer
        result = _coerce_value("42", "INTEGER")
        assert result == 42.0
        
        # Test invalid numeric
        result = _coerce_value("not_a_number", "DECIMAL")
        assert result == "not_a_number"
    
    def test_coerce_value_varchar(self):
        """Test _coerce_value with varchar types."""
        result = _coerce_value("test_string", "VARCHAR")
        assert result == "test_string"
        
        result = _coerce_value(None, "VARCHAR")
        assert result is None
    
    def test_parse_tabular_payload_success(self):
        """Test successful tabular payload parsing."""
        payload = {
            "data": [
                ["value1", "user1", "2024-01-01 12:00:00.000 UTC"],
                ["value2", "user2", "2024-01-02 13:00:00.000 UTC"]
            ],
            "metadata": {
                "value": {"placeInOrder": 0, "type": "VARCHAR"},
                "user": {"placeInOrder": 1, "type": "VARCHAR"},
                "timestamp": {"placeInOrder": 2, "type": "TIMESTAMP WITH TIME ZONE"}
            },
            "rowCount": 2
        }
        
        result = parse_tabular_payload(payload)
        
        assert "columns" in result
        assert "rows" in result
        assert "rowCount" in result
        assert result["columns"] == ["value", "user", "timestamp"]
        assert len(result["rows"]) == 2
        assert result["rows"][0]["value"] == "value1"
        assert result["rows"][0]["user"] == "user1"
        assert result["rows"][0]["timestamp"] == "2024-01-01T12:00:00Z"
        assert result["rowCount"] == 2
    
    def test_parse_tabular_payload_string_input(self):
        """Test parsing tabular payload from string."""
        payload_str = """{
            "data": [["test_value", "test_user"]],
            "metadata": {
                "value": {"placeInOrder": 0, "type": "VARCHAR"},
                "user": {"placeInOrder": 1, "type": "VARCHAR"}
            }
        }"""
        
        result = parse_tabular_payload(payload_str)
        
        assert len(result["rows"]) == 1
        assert result["rows"][0]["value"] == "test_value"
        assert result["rows"][0]["user"] == "test_user"
    
    def test_parse_tabular_payload_empty_data(self):
        """Test parsing tabular payload with empty data."""
        payload = {
            "data": [],
            "metadata": {}
        }
        
        result = parse_tabular_payload(payload)
        
        assert result["columns"] == []
        assert result["rows"] == []
    
    def test_parse_tabular_payload_with_passthrough_keys(self):
        """Test parsing with custom passthrough keys."""
        payload = {
            "data": [["value1"]],
            "metadata": {"value": {"placeInOrder": 0, "type": "VARCHAR"}},
            "customKey": "custom_value",
            "ignoredKey": "ignored_value"
        }
        
        result = parse_tabular_payload(payload, passthrough_keys=("customKey",))
        
        assert "customKey" in result
        assert result["customKey"] == "custom_value"
        assert "ignoredKey" not in result
    
    def test_parse_tabular_payload_no_type_coercion(self):
        """Test parsing without type coercion."""
        payload = {
            "data": [["123.45", "2024-01-01 12:00:00.000 UTC"]],
            "metadata": {
                "number": {"placeInOrder": 0, "type": "DECIMAL"},
                "timestamp": {"placeInOrder": 1, "type": "TIMESTAMP"}
            }
        }
        
        result = parse_tabular_payload(payload, coerce_types=False)
        
        assert result["rows"][0]["number"] == "123.45"  # String, not float
        assert result["rows"][0]["timestamp"] == "2024-01-01 12:00:00.000 UTC"  # String, not ISO
