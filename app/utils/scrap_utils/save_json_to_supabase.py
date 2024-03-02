from supabase import Client, create_client
import os


async def save_json_to_supabase(data, client_number, service):
    url: str = os.getenv("SUPABASE_URL")
    key: str = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    client = supabase.table("property").select("*").eq(service , client_number).execute()

    # Extract JSON from the column 'bills'
    bills = client.data[0]['bills']

    # Update JSON in the database
    supabase.table("property").update({"bills": data}).eq(service, client_number).execute()

    print("Data updated")