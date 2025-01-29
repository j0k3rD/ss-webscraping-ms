import httpx
from src.core.config import Config

HTTP_OK = 200
HTTP_CREATED = 201


async def make_request(method, url, data=None):
    """
    Make a request to the specified URL with the specified method.
    """
    async with httpx.AsyncClient() as client:
        if method in ["post", "put"]:
            response = await getattr(client, method)(url, json=data)
        else:
            response = await getattr(client, method)(url)
        if response.status_code not in {HTTP_OK, HTTP_CREATED}:
            raise Exception(f"Failed to {method} {url}: {response.status_code}")
        return response.json()


async def get_user_service_by_service(service_id):
    """
    Get all user_service by service ID.
    """
    users_service = await make_request(
        "get", f"{Config.BACKEND_URL}/user-service/service/{service_id}"
    )
    if not users_service:
        raise Exception("No user_service found")
    return users_service


async def get_services():
    """
    Get all services.
    """
    services = await make_request("get", f"{Config.BACKEND_URL}/service")
    if not services:
        raise Exception("No services found")
    return services
