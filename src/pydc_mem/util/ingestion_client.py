"""
Data Cloud Ingestion API Client

A simple client for ingesting key-value pairs into Salesforce Data Cloud.
"""

import httpx
import logging
from typing import Dict, Any
try:
    from pydc_auth import DataCloudTokenGenerator
except ImportError:
    # Mock for testing when pydc_auth is not available
    class DataCloudTokenGenerator:
        def get_dc_token(self):
            from types import SimpleNamespace
            return SimpleNamespace(
                access_token="mock_token",
                instance_url="https://mock-instance.salesforce.com"
            )

HTTP_SCHEME = 'https'
INGESTION_ENDPOINT = 'api/v1/ingest/sources'

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DataCloudIngestionClient:
    """Client for Salesforce Data Cloud Ingestion API"""

    def __init__(self, timeout: int = 30):
        """
        Initialize the Data Cloud Ingestion Client

        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.token_generator = DataCloudTokenGenerator()
        self.auth_token_response = None
        self.timeout = timeout

        # Initialize HTTP client with common headers
        self.client = httpx.Client(
            timeout=timeout
        )

    def ingest_data(self, data: Dict[str, Any], connector: str, dlo: str) -> Dict[str, Any]:
        """
        Ingest a key-value pair into Data Cloud

        Args:
            data: data to be uploaded
            connector: Ingestion api connector's api_name
            dlo: name of the DLO to which the Data needs to be uploaded.
        Returns:
            Dict containing the API response

        Raises:
            httpx.HTTPStatusError: If the API request fails
            httpx.RequestError: If there's a network error
        """
        dc_token_response = self.token_generator.get_dc_token()
        url = f"{HTTP_SCHEME}://{dc_token_response.instance_url}/{INGESTION_ENDPOINT}/{connector}/{dlo}"

        headers = {
            'Authorization': f'Bearer {dc_token_response.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            print(f"Invoking ingestion api on url: {url}, with data: {data}, and headers: {headers}")
            response = self.client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            raise httpx.HTTPStatusError(error_msg, request=e.request, response=e.response)
        except httpx.RequestError as e:
            raise httpx.RequestError(f"Network error: {str(e)}")

    def close(self):
        """Close the HTTP client"""
        self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()