import json, httpx
from src.core.config import Config


async def make_request(method, url, data=None):
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


async def save_bills(user_service_id, bills, debt=False):
    print(f"user_service_id: {user_service_id}")

    user_service = await make_request(
        "get", f"{Config.BACKEND_URL}/user-service/{user_service_id}"
    )
    if not user_service:
        return False

    scrapped_data = await make_request(
        "get", f"{Config.BACKEND_URL}/scrapped-data/user-service/{user_service_id}"
    )

    bills_to_save = []
    if scrapped_data:
        # Process existing data
        existing_bills = scrapped_data.get("bills_url", [])
        for bill in bills:
            if json.dumps(bill) not in [
                json.dumps(existing_bill) for existing_bill in existing_bills
            ]:
                bills_to_save.append(bill)
    else:
        # No existing data, save all bills
        bills_to_save = bills
        scrapped_data = {
            "user_service_id": user_service_id,
            "bills_url": [],
            "consumption_data": {},
        }
        # print(f"bills_to_save: {bills_to_save}")
    if bills_to_save:
        scrapped_data["bills_url"].extend(bills_to_save)
        api_endpoint = f"{Config.BACKEND_URL}/scrapped-data/"

        result = await make_request(
            "post" if not scrapped_data.get("id") else "patch",
            api_endpoint,
            data=scrapped_data,
        )

        if not result:
            print(f"Failed to save bills for user_service_id: {user_service_id}")
            return False

        return True

    return True
