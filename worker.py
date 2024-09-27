import os
import asyncio
from celery import Celery
from celery.schedules import crontab
import ast
from src.utils.browser_invoker import InvokerBrowser
from src.services.scrap_service import ScrapService
from src.services.extract_data_service import ExtractDataService
from src.utils.worker_utils.req_backend import get_services, get_providers_by_service
from src.utils.worker_utils.req_backend import get_providers_by_service
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

celery = Celery(__name__)
celery.conf.enable_utc = True
celery.conf.timezone = "UTC"
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379")
celery.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://redis:6379"
)


@celery.task(name="scrap_task")
def scrap_task(data: dict):
    # Primero ejecutamos scrap_task
    invoker = InvokerBrowser()
    browser_data = data["browser"]
    browser = browser_data.lower()
    browser_web = invoker.get_command(browser)
    scrap_service = ScrapService(browser_web)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrap_service.search(data))

    print(result)

    if result[1] != "No new bills to save":
        # Luego ejecutamos extract_data_task con el resultado de scrap_task
        try:
            extract_service = ExtractDataService()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(extract_service.plumb_bills(data))
            return {"status": "success"}

        except Exception as e:
            return {"error": f"Error: {e}"}
    else:
        return {"status": "success"}


@celery.task
def scrap_all_providers_by_service_task(service):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    service_id = service["id"]
    providers = loop.run_until_complete(get_providers_by_service(service_id))
    if providers == "No providers found":
        return {"error": "No providers found"}

    invoker = InvokerBrowser()
    browser_web = invoker.get_command(os.getenv("BROWSER"))
    scrap_service = ScrapService(browser_web)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for provider in providers:
        data = {
            "browser": os.getenv("BROWSER"),
            "provider_client": provider,
            "service": service,
        }
        result = loop.run_until_complete(scrap_service.search(data))
        print(result)
    # Luego ejecutamos extract_data_task con el resultado de scrap_all_providers_task
    if result[1] != "No new bills to save":
        try:
            extract_service = ExtractDataService()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(extract_service.plumb_bills(data))
            return {"status": "success"}

        except Exception as e:
            return {"error": f"Error: {e}"}
    else:
        return {"status": "success"}


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    services = loop.run_until_complete(get_services())
    print("Services: ", services)
    for service in services:
        crondict = ast.literal_eval(service["crontab"])
        minute = list(crondict["minute"])[0]
        hour = list(crondict["hour"])[0]
        day_of_week = ",".join(map(str, crondict["day_of_week"]))
        day_of_month = ",".join(map(str, crondict["day_of_month"]))
        month_of_year = ",".join(map(str, crondict["month_of_year"]))
        sender.add_periodic_task(
            crontab(
                minute=f"{minute}",
                hour=f"{hour}",
                day_of_week=f"{day_of_week}",
                day_of_month=f"{day_of_month}",
                month_of_year=f"{month_of_year}",
            ),
            scrap_all_providers_by_service_task.s(service),
            name=f"Scraping {service['company_name']} every minute",
        )
