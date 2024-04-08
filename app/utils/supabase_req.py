from supabase import Client, create_client
import os

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def get_user_data(user_id: str, property_id: str):
    result = (
        supabase.table("property")
        .select("*")
        .eq("user_id", user_id)
        .eq("id", property_id)
        .execute()
    )
    return result.data
