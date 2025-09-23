"""
Test configuration and fixtures for pydcmem tests.
"""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
import json
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

# Set test environment variables
os.environ.update({
    "OPENAI_API_KEY": "test-api-key",
    "MEMORY_DLO": "test_dlo",
    "MEMORY_CONNECTOR": "test_connector",
    "VECTOR_IDX_DLM": "test_vector_index",
    "CHUNK_DLM": "test_chunk_dlm",
    "SALESFORCE_ORGANIZATION_ID": "test_org_id"
})

# Global mock for OpenAI client
@pytest.fixture(autouse=True)
def mock_openai_globally():
    """Automatically mock OpenAI client for all tests."""
    with patch('pydc_mem.core.memory_extractor.OpenAI') as mock_openai_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps([
            {"entity": "User", "attribute": "preferred_airline", "value": "Delta Airlines"},
            {"entity": "User", "attribute": "seat_preference", "value": "window"}
        ])
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([
        {"entity": "User", "attribute": "preferred_airline", "value": "Delta Airlines"},
        {"entity": "User", "attribute": "seat_preference", "value": "window"}
    ])
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_httpx_response():
    """Mock httpx response for testing."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            ["attr1", "value1", "user1"],
            ["attr2", "value2", "user1"]
        ],
        "metadata": {
            "attr1": {"placeInOrder": 0, "type": "VARCHAR"},
            "value1": {"placeInOrder": 1, "type": "VARCHAR"},
            "user1": {"placeInOrder": 2, "type": "VARCHAR"}
        }
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def sample_memory_candidates():
    """Sample memory candidates for testing."""
    from pydc_mem.core.memory_extractor import MemoryCandidate
    
    return [
        MemoryCandidate(entity="User", attribute="preferred_airline", value="Delta Airlines"),
        MemoryCandidate(entity="User", attribute="seat_preference", value="window"),
        MemoryCandidate(entity="User", attribute="meal_preference", value="vegetarian")
    ]


@pytest.fixture
def sample_user_attributes():
    """Sample user attributes data for testing."""
    return [
        {
            "id__c": "attr1",
            "attribute__c": "preferred_airline",
            "value__c": "Delta Airlines",
            "userId__c": "user123"
        },
        {
            "id__c": "attr2", 
            "attribute__c": "seat_preference",
            "value__c": "window",
            "userId__c": "user123"
        }
    ]


@pytest.fixture
def mock_data_cloud_token():
    """Mock Data Cloud token response."""
    mock_token = Mock()
    mock_token.access_token = "test_access_token"
    mock_token.instance_url = "https://test-instance.salesforce.com"
    return mock_token


@pytest.fixture
def mock_salesforce_token():
    """Mock Salesforce token response."""
    mock_token = Mock()
    mock_token.access_token = "test_sf_token"
    mock_token.instance_url = "https://test-instance.salesforce.com"
    return mock_token
