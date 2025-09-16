"""
Data Cloud Query Svc API Client
Given a SQL Query return the query results from Data Cloud's Query Svc API.
"""
import httpx
import logging
from typing import Dict, Any, List
from pydantic import BaseModel
from pydc_auth import SalesforceTokenGenerator

QUERY_SVC_ENDPOINT = 'services/data/v63.0/ssot/queryv2'

logger = logging.getLogger(__name__)


class QueryOutput(BaseModel):
    id: str
    score: float
    payload: str


class QueryServiceClient:
    """Client for Salesforce Data Cloud's Query Service API"""

    def __init__(self, timeout: int = 30):
        """
        Initialize the Data Cloud Query Service Client

        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.token_generator = SalesforceTokenGenerator()
        self.auth_token_response = None
        self.timeout = timeout

        # Initialize HTTP client with common headers
        self.client = httpx.Client(
            timeout=timeout
        )

    def read_data(self, data: Dict[str, Any]) -> List[QueryOutput]:
        """
        Execute the given SQL Query and return the query results from Data Cloud's Query Svc API.

        Args:
            data: json with SQL query. e.g. {'sql': 'select * from universe'}
        Returns:
            Dict containing the API response

        Raises:
            httpx.HTTPStatusError: If the API request fails
            httpx.RequestError: If there's a network error
        """
        sf_token_response = self.token_generator.get_sf_token()
        url = f"{sf_token_response.instance_url}/{QUERY_SVC_ENDPOINT}"

        headers = {
            'Authorization': f'Bearer {sf_token_response.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            logger.debug(f"Invoking query svc api on url: {url}, with data: {data}, and headers: {headers}")
            response = self.client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response
            # items = response.json()['data']
            # output = []
            # for item in items:
            #     output.append(QueryOutput(
            #         id=item[0],
            #         score=item[1],
            #         payload=item[2]
            #     ))
            # return output

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            raise httpx.HTTPStatusError(error_msg, request=e.request, response=e.response)
        except httpx.RequestError as e:
            raise httpx.RequestError(f"Network error: {str(e)}")