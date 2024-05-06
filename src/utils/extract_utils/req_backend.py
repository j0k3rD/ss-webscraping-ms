import os
import tempfile
import requests
import httpx
import json

BASE_URL = "http://localhost:5000"


async def make_request(method, url, data=None):
    async with httpx.AsyncClient() as client:
        if method in ['post', 'put', 'patch']:
            response = await getattr(client, method)(url, json=data)
        else:
            response = await getattr(client, method)(url)
        if response.status_code not in {200, 201}:
            print(f"Failed to {method} {url}: {response.status_code}")
            return None
        return response.json()


async def get_provider(provider_id):
    provider = await make_request('get', f"{BASE_URL}/provider-clients/{provider_id}")
    if not provider:
        return 'Provider not found'


async def get_data_by_provider_id(provider_id):
    await get_provider(provider_id)
    
    scrapped_data = await make_request('get', f"{BASE_URL}/scrapped-datas/provider-client/{provider_id}")
    if not scrapped_data:
        return 'No Scrapped Data found'
    
    return scrapped_data


async def save_consumed_data(provider_id, consumed_data):
    scrapped_data = await get_data_by_provider_id(provider_id)

    scrapped_data_id = scrapped_data.get('id')
    bills = scrapped_data.get('bills', [])

    consumption_to_save = []
    for consumption in consumed_data:
        if json.dumps(consumption) not in [json.dumps(existing_consumption) for existing_consumption in bills]:
            consumption_to_save.append(consumption)

    if not consumption_to_save:
        return 'No new data to save'

    data = {
        "id": scrapped_data_id,
        "provider_client_id": provider_id,
        "consumption_data": consumed_data,
        "bills": bills
    }
    
    response = await make_request('put', f"{BASE_URL}/scrapped-datas/{scrapped_data_id}", data)
    if not response:
        return 'Failed to save data'
    else:
        return 'Data saved'

async def download_pdf(provider_client_id: str):
    data = await get_data_by_provider_id(provider_client_id)
    bills = data.get('bills', [])

    c = 1
    temp_dir = tempfile.mkdtemp()
    for bill in bills:
        url = bill['url']
        response = requests.get(url)
        with open(os.path.join(temp_dir, f"{c}.pdf"), "wb") as file:
            file.write(response.content)
            c += 1
    return temp_dir
