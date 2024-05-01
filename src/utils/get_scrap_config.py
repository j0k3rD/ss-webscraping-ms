from fastapi import APIRouter
import httpx

util = APIRouter()

URL = "http://127.0.0.1:5000"


async def get_service_data(id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{URL}/services/{id}")
        return response.json()

#TODO: Traerlo con el user_id, ahora para test directamente con el id
async def get_provider_data(id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{URL}/provider-clients/{id}")
        return response.json()
    
@util.get("/services")
async def get_services():
    id = 10
    return await get_service_data(id)

@util.get("/provider-clients")
async def get_provider_clients():
    id = 1
    return await get_provider_data(id)