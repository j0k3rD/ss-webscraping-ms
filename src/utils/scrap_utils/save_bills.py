import json, httpx
from datetime import datetime

BASE_URL = "http://localhost:5000"

async def make_request(method, url, data=None):
    async with httpx.AsyncClient() as client:
        if method in ['post', 'put']:
            response = await getattr(client, method)(url, json=data)
        else:
            response = await getattr(client, method)(url)
        if response.status_code not in {200, 201}:
            print(f"Failed to {method} {url}: {response.status_code}")
            return None
        return response.json()

async def save_bills(provider_client_id, bills):
    # Buscar provider_client_id
    provider_client = await make_request('get', f"{BASE_URL}/provider-clients/{provider_client_id}")
    if not provider_client:
        return

    # Buscar scrapped_data_id con provider_client_id
    scrapped_data_id = await make_request('get', f"{BASE_URL}/scrapped-datas/provider-client/{provider_client_id}")

    # Crear o actualizar scrapped_data
    data = {
        "provider_client_id": provider_client_id,
        "bills": bills
    }
    print('BILSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS',data['bills'])
    if scrapped_data_id:
        print("Scrapped_data", scrapped_data_id['id'])
        # Actualizar scrapped_data
        response = await make_request('put', f"{BASE_URL}/scrapped-datas/{scrapped_data_id['id']}", data)
        if response:
            print("Bills saved successfully")
    else:
        # Crear scrapped_data
        response = await make_request('post', f"{BASE_URL}/scrapped-data", data)
        if response:
            print("Scrapped_data created successfully")