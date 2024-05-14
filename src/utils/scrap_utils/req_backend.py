import json, httpx, os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BACKEND_URL")


async def make_request(method, url, data=None):
    async with httpx.AsyncClient() as client:
        if method in ["post", "put"]:
            response = await getattr(client, method)(url, json=data)
        else:
            response = await getattr(client, method)(url)
        if response.status_code not in {200, 201}:
            print(f"Failed to {method} {url}: {response.status_code}")
            return None
        return response.json()


async def save_bills(provider_client_id, bills):
    # Buscar provider_client_id
    provider_client = await make_request(
        "get", f"{BASE_URL}/provider-client/{provider_client_id}"
    )
    if not provider_client:
        return
    # Buscar scrapped_data_id con provider_client_id
    scrapped_data_id = await make_request(
        "get", f"{BASE_URL}/scrapped-datas/provider-client/{provider_client_id}"
    )

    if scrapped_data_id:
        consumption_data = scrapped_data_id.get("consumption_data", [])
        # Comparar las facturas que ya están en la base de datos con las nuevas facturas
        bills_to_save = []
        for bill in bills:
            if json.dumps(bill) not in [
                json.dumps(existing_bill) for existing_bill in scrapped_data_id["bills"]
            ]:
                bills_to_save.append(bill)

        if not bills_to_save:
            return "No new bills to save"

        # Crear data
        data = {
            "provider_client_id": provider_client_id,
            "bills": bills_to_save,
            "consumption_data": consumption_data,
        }
        response = await make_request(
            "put", f"{BASE_URL}/scrapped-datas/{scrapped_data_id['id']}", data
        )
        if not response:
            print("Failed to save bills")
        else:
            print("Bills saved successfully")
    else:
        # Crear scrapped_data
        data = {"provider_client_id": provider_client_id, "bills": bills}
        response = await make_request("post", f"{BASE_URL}/scrapped-data", data)
        if response:
            return "Scrapped_data created successfully"
