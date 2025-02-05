from typing import Optional, Any, Dict, Union, List
import logging
import httpx
from fastapi import HTTPException
from src.core.errors import HTTPClientError
from src.core.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainServiceClient:
    """Client for interacting with the main microservice."""

    def __init__(self):
        self.base_url = Config.BACKEND_URL
        self.timeout = 30
        self.headers = {
            "X-Internal-API-Key": Config.INTERNAL_API_KEY,
            "Content-Type": "application/json",
        }       

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Any:
        """
        Make an HTTP request to the main service.

        Args:
            method: HTTP method to use
            endpoint: API endpoint to call
            data: Request body data
            params: Query parameters

        Returns:
            Response data from the API

        Raises:
            HTTPClientError: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, headers=self.headers, follow_redirects=True
            ) as client:
                logger.info(f"Making {method} request to {url}")

                request_kwargs = {}
                if data is not None:
                    request_kwargs["json"] = data
                if params is not None:
                    request_kwargs["params"] = params

                response = await getattr(client, method.lower())(url, **request_kwargs)

                # Handle redirects
                if response.status_code == 307:
                    redirect_url = response.headers.get("location")
                    logger.info(f"Following redirect to {redirect_url}")
                    return await self._make_request(method, redirect_url, data, params)

                # Raise for bad responses
                response.raise_for_status()

                return response.json()

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error occurred: {str(e)}"
            logger.error(error_msg)
            if e.response.status_code == 403:
                raise HTTPException(
                    status_code=403, detail="Service authentication failed"
                )
            raise HTTPClientError(error_msg, e.response.status_code, e.response)

        except httpx.RequestError as e:
            error_msg = f"Request error occurred: {str(e)}"
            logger.error(error_msg)
            raise HTTPClientError(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error occurred: {str(e)}"
            logger.error(error_msg)
            raise HTTPClientError(error_msg)

    # User Service Methods
    async def get_user_service(self, user_service_id: int) -> Dict:
        """Get user service by ID."""
        return await self._make_request("GET", f"user-service/{user_service_id}")

    async def get_user_services_by_service(self, service_id: int) -> List[Dict]:
        """Get all user services for a service ID."""
        return await self._make_request("GET", f"user-service/service/{service_id}")

    # Scrapped Data Methods
    async def get_scrapped_data(self, user_service_id: int) -> Union[Dict, List[Dict]]:
        """Get scrapped data for a user service."""
        return await self._make_request(
            "GET", f"scrapped-data/user-service/{user_service_id}"
        )

    async def create_scrapped_data(
        self,
        user_service_id: int,
        bills: List[Dict],
        consumption_data: Dict = None,
        debt: bool = False,
    ) -> Dict:
        """Create new scrapped data."""
        data = {
            "user_service_id": user_service_id,
            "bills_url": bills,
            "consumption_data": consumption_data or {},
            "debt": debt,
        }
        return await self._make_request("POST", "scrapped-data", data)

    async def update_scrapped_data(
        self,
        scrapped_data_id: int,
        bills: List[Dict] = None,
        consumption_data: Dict = None,
        debt: Optional[bool] = None,
    ) -> Dict:
        """Update existing scrapped data."""
        data = {}
        if bills is not None:
            data["bills_url"] = bills
        if consumption_data is not None:
            data["consumption_data"] = consumption_data
        if debt is not None:
            data["debt"] = debt

        return await self._make_request(
            "PATCH", f"scrapped-data/{scrapped_data_id}", data
        )

    # Service Methods
    async def get_services(self) -> List[Dict]:
        """Get all services."""
        return await self._make_request("GET", "service")
