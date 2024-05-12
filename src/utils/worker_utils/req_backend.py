import json, httpx

BASE_URL = "http://localhost:5000"
HTTP_OK = 200
HTTP_CREATED = 201

async def make_request(method, url, data=None):
    """
    Make a request to the specified URL with the specified method.
    """
    async with httpx.AsyncClient() as client:
        if method in ['post', 'put']:
            response = await getattr(client, method)(url, json=data)
        else:
            response = await getattr(client, method)(url)
        if response.status_code not in {HTTP_OK, HTTP_CREATED}:
            raise Exception(f"Failed to {method} {url}: {response.status_code}")
        return response.json()
    

async def get_providers_by_service(service_id):
    """
    Get providers by service ID.
    """
    providers = await make_request('get', f"{BASE_URL}/provider-clients/service/{service_id}")
    if not providers:
        raise Exception('No providers found')
    return providers        


async def get_services():
    """
    Get all services.
    """
    services = await make_request('get', f"{BASE_URL}/services")
    if not services:
        raise Exception('No services found')
    return services