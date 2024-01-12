from celery import Celery
from app.services.scrap_services_aysam import ScrapServicesAySaM
from app.services.scrap_service_ctnet import ScrapServicesCTNET
from app.services.scrap_services_ecogas import ScrapServicesEcogas
from app.services.scrap_services_edemsa import ScrapServicesEdemsa
from supabase import Client, create_client
import os
from .utils.browser_invoker import InvokerBrowser

app = Celery("tasks", broker="redis://localhost:6379/0")

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def get_user_data(user_id: str, property_id: str):
    result = (
        supabase.table("providers_ids")
        .select("*")
        .eq("user_id", user_id)
        .eq("property_id", property_id)
        .execute()
    )
    return result.data


@app.task
def scrap_ctnet_task(browser, client_number):
    invoker = InvokerBrowser()
    browser = browser.lower()
    print(browser)
    browser_web = invoker.get_command(browser)
    scrap_service = ScrapServicesCTNET(browser_web)
    result = scrap_service.search(client_number)
    return result


# @app.task
# def scrap_aysam_task(client_number):
#     browser = Browser()
#     scrap_service = ScrapServicesAySaM(browser)
#     result = scrap_service.search(client_number)
#     scrap_service.close_browser()
#     return result


# @app.task
# def scrap_ecogas_task(client_number):
#     browser = Browser()
#     scrap_service = ScrapServicesEcogas(browser)
#     result = scrap_service.search(client_number)
#     scrap_service.close_browser()
#     return result


# @app.task
# def scrap_edemsa_task(client_number):
#     browser = Browser()
#     scrap_service = ScrapServicesEdemsa(browser)
#     result = scrap_service.search(client_number)
#     scrap_service.close_browser()
#     return result


@app.task
def scrap_task(browser: str, user_id: str, property_id: int):
    user_data = get_user_data(user_id, property_id)

    if user_data:
        internet_provider_id = user_data[0]["internet_provider_id"]
        print(internet_provider_id)
        result = scrap_ctnet_task(browser, internet_provider_id)
        return result
    else:
        return None
