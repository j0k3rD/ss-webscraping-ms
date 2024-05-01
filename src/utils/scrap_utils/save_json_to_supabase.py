# from supabase import Client, create_client
# import os


# async def save_json_to_supabase(data, client_number):
#     url: str = os.getenv("SUPABASE_URL")
#     key: str = os.getenv("SUPABASE_KEY")
#     supabase: Client = create_client(url, key)

#     client = (
#         supabase.table("provider_client")
#         .select("*")
#         .eq("client_number", client_number)
#         .execute()
#     )
#     company_id = client.data[0]["company_id"]
#     # Extract JSON from the column 'bills'
#     bills = client.data[0]["bills"]

#     # Append new JSON to the existing JSON
#     if bills == None:
#         updated_bill = data
#     else:
#         # Convert bills and data to sets of URLs
#         bills_urls = set(bill["url"] for bill in bills)
#         data_urls = set(datum["url"] for datum in data)

#         # Perform a union of the two sets
#         updated_urls = bills_urls | data_urls

#         # Convert the result back to the required format
#         updated_bill = [{"url": url} for url in updated_urls]

#     # Update JSON in the database
#     supabase.table("provider_client").update({"bills": updated_bill}).eq(
#         "company_id", company_id
#     ).eq("client_number", client_number).execute()

#     print("Data updated")
