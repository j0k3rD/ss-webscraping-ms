from celery import Celery
from app.services.scrap_debt_services_aysam import ScrapDebtServicesAySaM
from app.services.scrap_debt_service_ctnet import ScrapDebtServicesCTNET
from app.services.scrap_debt_services_ecogas import ScrapDebtServicesEcogas
from app.services.scrap_debt_services_edemsa import ScrapDebtServicesEdemsa
from supabase import Client, create_client
import os
from .utils.browser_invoker import InvokerBrowser
import asyncio

app = Celery("tasks", broker="redis://localhost:6379/0")

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


@app.task
def scrap_ctnet_task(browser, client_number):
    invoker = InvokerBrowser()
    browser = browser.lower()
    print(browser)
    browser_web = invoker.get_command(browser)
    scrap_service = ScrapDebtServicesCTNET(browser_web)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrap_service.search(client_number))
    print(result)
    return result


@app.task
def scrap_aysam_task(browser, client_number):
    invoker = InvokerBrowser()
    browser = browser.lower()
    print(browser)
    browser_web = invoker.get_command(browser)
    scrap_service = ScrapDebtServicesAySaM(browser_web)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrap_service.search(client_number))
    print(result)
    return result


@app.task
def scrap_ecogas_task(browser, client_number):
    invoker = InvokerBrowser()
    browser = browser.lower()
    print(browser)
    browser_web = invoker.get_command(browser)
    scrap_service = ScrapDebtServicesEcogas(browser_web)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrap_service.search(client_number))
    print(result)
    return result


@app.task
def scrap_edemsa_task(browser, client_number):
    invoker = InvokerBrowser()
    browser = browser.lower()
    print(browser)
    browser_web = invoker.get_command(browser)
    scrap_service = ScrapDebtServicesEdemsa(browser_web)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrap_service.search(client_number))
    print(result)
    return result


#!TODO: Scrapeo solamente cuando se crea un nuevo client_number, sino traer ultimo scrapeo del mes de la db.
@app.task
def scrap_by_service(browser: str, user_id: str, property_id: str, service: str):
    user_data = get_user_data(user_id, property_id)

    if not user_data:
        raise Exception("User not found")

    if service == "aysam":
        result = scrap_aysam_task.delay(browser, user_data[0]["water_provider_id"])
    elif service == "ctnet":
        result = scrap_ctnet_task.delay(browser, user_data[0]["internet_provider_id"])
    elif service == "ecogas":
        result = scrap_ecogas_task.apply_async(
            args=[browser, user_data[0]["gas_provider_id"]], soft_time_limit=30
        )
    elif service == "edemsa":
        result = scrap_edemsa_task.apply_async(
            args=[browser, user_data[0]["electricity_provider_id"]], soft_time_limit=30
        )
    else:
        raise Exception("Service not found")

    return result


@app.task
def scrap_all(browser: str, user_id: str, property_id: str):
    user_data = get_user_data(user_id, property_id)

    result = None

    if not user_data:
        raise Exception("User not found")

    if user_data[0]["water_provider_id"]:
        result = scrap_aysam_task.delay(browser, user_data[0]["water_provider_id"])
    if user_data[0]["internet_provider_id"]:
        result = scrap_ctnet_task.delay(browser, user_data[0]["internet_provider_id"])
    if user_data[0]["gas_provider_id"]:
        result = scrap_ecogas_task.apply_async(
            args=[browser, user_data[0]["gas_provider_id"]], soft_time_limit=120
        )
    if user_data[0]["electricity_provider_id"]:
        result = scrap_edemsa_task.apply_async(
            args=[browser, user_data[0]["electricity_provider_id"]], soft_time_limit=120
        )
    return result
