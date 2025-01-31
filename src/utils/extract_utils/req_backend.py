import asyncio
import os
import tempfile
import json
import httpx
from src.core.config import Config


async def make_request(method, url, data=None):
    """Realiza una solicitud HTTP y maneja errores."""
    async with httpx.AsyncClient() as client:
        try:
            if method == "get":
                response = await client.get(url)
            elif method == "post":
                response = await client.post(url, json=data)
            elif method == "patch":
                response = await client.patch(url, json=data)
            else:
                response = await getattr(client, method)(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Failed to {method} {url}: {e.response.status_code}")
            if e.response.status_code == 403:
                print("Authorization error: Ensure you have the necessary permissions.")
            return None
        except Exception as e:
            print(f"Unexpected error during {method} request to {url}: {e}")
            return None


async def get_user_service(user_service_id):
    """Obtiene los datos del servicio de usuario."""
    user_service = await make_request(
        "get", f"{Config.BACKEND_URL}/user-service/{user_service_id}"
    )
    if not user_service:
        print("No User Service found")
        return None
    return user_service


async def get_data_by_user_service_id(user_service_id):
    """Obtiene los datos raspados por ID de servicio de usuario."""
    scrapped_data = await make_request(
        "get", f"{Config.BACKEND_URL}/scrapped-data/user-service/{user_service_id}"
    )
    if not scrapped_data:
        print("No Scrapped Data found")
        return None

    if isinstance(scrapped_data, list):
        return scrapped_data[0]
    return scrapped_data


async def save_consumed_data(user_service_id, consumed_data):
    print("SAVE CONSUMED DATA")
    """Guarda los datos de consumo en el backend."""
    scrapped_data = await get_data_by_user_service_id(user_service_id)
    print(f"Consumed data: {consumed_data}")
    if not isinstance(scrapped_data, dict):
        print(f"Unexpected data type for scrapped_data: {type(scrapped_data)}")
        return "Failed to save data"

    scrapped_data_id = scrapped_data.get("id")
    if not scrapped_data_id:
        print("Scrapped Data ID not found")
        return "Failed to save data"

    # Handle bills_url as a list
    bills_url = scrapped_data.get("bills_url", [])
    # print(f"bills_url: {bills_url}")
    if isinstance(bills_url, list):
        bills = bills_url  # Use the list directly
    elif isinstance(bills_url, dict):
        bills = bills_url.get("bills", [])  # Fallback to dictionary handling
    else:
        print(f"Unexpected data type for bills_url: {type(bills_url)}")
        return "Failed to save data"

    # Convert existing bills to JSON strings for comparison
    existing_bills = [json.dumps(bill) for bill in bills]
    consumption_to_save = [
        consumption
        for consumption in consumed_data
        if json.dumps(consumption) not in existing_bills
    ]

    if not consumption_to_save:
        return "No new data to save"

    # Prepare data for the PATCH request
    print(f"Consumption to save: {consumption_to_save}")
    data = {
        "consumption_data": consumed_data,
    }
    print(f"Data to save: {data}")
    # Send the PATCH request to update the backend
    response = await make_request(
        "patch", f"{Config.BACKEND_URL}/scrapped-data/{scrapped_data_id}", data
    )
    if not response:
        return "Failed to save data"
    return "Data saved"


async def download_pdf(url_bills):
    """Descarga los PDFs asociados a un servicio de usuario."""
    if not isinstance(url_bills, list):
        print(f"Unexpected data type for url_bills: {type(url_bills)}")
        return None

    temp_dir = tempfile.mkdtemp()
    contents = []

    # Download all PDFs in parallel
    async with httpx.AsyncClient() as client:
        tasks = [
            download_single_pdf(client, bill["url"], temp_dir, i)
            for i, bill in enumerate(url_bills, start=1)
        ]
        downloaded_files = await asyncio.gather(*tasks)

    # Add downloaded files to contents
    contents.extend([file for file in downloaded_files if file is not None])

    print(f"Downloaded files: {contents}")
    return contents


async def download_single_pdf(client, url, temp_dir, index):
    """Descarga un solo PDF y lo guarda en el directorio temporal."""
    try:
        response = await client.get(url)
        response.raise_for_status()
        file_path = os.path.join(temp_dir, f"{index}.pdf")
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    except httpx.HTTPStatusError as e:
        print(f"Failed to download PDF from {url}: {e}")
        return None
