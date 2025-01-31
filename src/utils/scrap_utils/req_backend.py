import json
import httpx
from src.core.config import Config
from typing import Dict, Any, Optional, List


async def make_request(
    method: str, url: str, data: Optional[Dict] = None
) -> Optional[Any]:
    """
    Realiza una solicitud HTTP asíncrona.
    """
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            if method in ["post", "patch"]:
                response = await getattr(client, method)(url, json=data)
            else:
                response = await getattr(client, method)(url)

            if response.status_code == 404:
                print(f"Resource not found at {url}")
                return None

            if response.status_code not in {200, 201, 307}:
                print(f"Failed to {method} {url}: {response.status_code}")
                return None

            if response.status_code == 307:
                redirect_url = response.headers.get("location")
                return await make_request(method, redirect_url, data)

            return response.json()
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None


async def save_bills(
    user_service_id: int, bills: List[Dict], debt: bool = False
) -> Dict[str, Any]:
    """
    Guarda las facturas en el backend y devuelve un resultado estructurado.
    """
    print(f"BIlls: {bills}")

    # Verificar si el user_service existe
    user_service = await make_request(
        "get", f"{Config.BACKEND_URL}/user-service/{user_service_id}"
    )
    if not user_service:
        return {
            "success": False,
            "message": "User service not found",
            "new_bills_saved": False,
        }

    # Obtener scrapped_data existente
    scrapped_data = await make_request(
        "get", f"{Config.BACKEND_URL}/scrapped-data/user-service/{user_service_id}"
    )
    # Si no existe scrapped_data, crear un nuevo registro
    if not scrapped_data:
        new_scrapped_data = {
            "user_service_id": user_service_id,
            "bills_url": bills,  # Guardar todas las facturas nuevas
            "consumption_data": {},
        }
        response = await make_request(
            "post", f"{Config.BACKEND_URL}/scrapped-data", new_scrapped_data
        )
        if not response:
            return {
                "success": False,
                "message": "Failed to create scrapped data",
                "new_bills_saved": False,
            }
        return {
            "success": True,
            "message": "New scrapped data created with bills",
            "new_bills_saved": True,
        }

    # Ensure scrapped_data is a list
    if not isinstance(scrapped_data, list):
        scrapped_data = [scrapped_data]

    for data in scrapped_data:
        # Ensure bills_url is a list within the dictionary
        if not isinstance(data.get("bills_url"), list):
            data["bills_url"] = []

        # Ensure bills is a list
        if isinstance(bills, dict):
            bills = [bills]
        elif not isinstance(bills, list):
            print(f"Invalid data type for bills: {type(bills)}")
            return {
                "success": False,
                "message": "Invalid data type for bills, expected a list or dict",
                "new_bills_saved": False,
            }

        print(f"bills: {bills}")
        print(f"scrapped_data_id: {data['id']}")

        bills_to_save = []
        existing_bills = data.get("bills_url", [])
        for bill in bills:
            if json.dumps(bill) not in [
                json.dumps(existing_bill) for existing_bill in existing_bills
            ]:
                bills_to_save.append(bill)

        if bills_to_save:
            data["bills_url"].extend(bills_to_save)
            print(f"DATA: {data}")
            # Organizar la información para la solicitud PATCH
            data = {
                "bills_url": {"bills": data["bills_url"]},
                "consumption_data": data["consumption_data"],
            }
            response = await make_request(
                "patch",
                f"{Config.BACKEND_URL}/scrapped-data/{data['id']}",
                data,
            )
            if not response:
                return {
                    "success": False,
                    "message": "Failed to update scrapped data",
                    "new_bills_saved": False,
                }
            return {
                "success": True,
                "message": "New bills saved successfully",
                "new_bills_saved": True,
            }
        else:
            return {
                "success": True,
                "message": "No new bills to save",
                "new_bills_saved": False,
            }
