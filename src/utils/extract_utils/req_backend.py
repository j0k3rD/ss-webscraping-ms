import json
from src.core.config import Config
from src.services.http_client import MainServiceClient

client = MainServiceClient()


async def save_consumed_data(user_service_id, consumed_data):
    """Guarda los datos de consumo en el backend."""
    scrapped_data = await client.get_scrapped_data(user_service_id)
    if not isinstance(scrapped_data, dict):
        print(f"Unexpected data type for scrapped_data: {type(scrapped_data)}")
        return "Failed to save data"

    scrapped_data_id = scrapped_data.get("id")
    if not scrapped_data_id:
        print("Scrapped Data ID not found")
        return "Failed to save data"

    # Handle bills_url as a list
    bills_url = scrapped_data.get("bills_url", [])
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
    data = {
        "consumption_data": consumed_data,
    }
    # Send the PATCH request to update the backend
    response = await client.make_request(
        "patch", f"{Config.BACKEND_URL}/scrapped-data/{scrapped_data_id}", data
    )
    if not response:
        return "Failed to save data"
    return "Data saved"
