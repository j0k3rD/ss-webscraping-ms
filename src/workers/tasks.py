import asyncio
from celery import Celery
from celery.schedules import crontab
import ast
from src.utils.browser_invoker import InvokerBrowser
from src.services.scrap_service import ScrapService
from src.services.extract_data_service import ExtractDataService
from src.utils.worker_utils.req_backend import get_services, get_user_service_by_service
from src.utils.worker_utils.req_backend import get_user_service_by_service
from src.core.config import Config

c_app = Celery()
c_app.config_from_object("src.core.config")


@c_app.task(name="scrap_task")
def scrap_task(data: dict):
    # Primero ejecutamos scrap_task
    scrap_service = ScrapService()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrap_service.search(data))

    print("Result: ", result)

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


@c_app.task
def scrap_all_user_service_by_service_task(service):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    service_id = service["id"]
    users_service = loop.run_until_complete(get_user_service_by_service(service_id))
    if users_service == "No user_service found":
        return {"error": "No user_service found"}

    invoker = InvokerBrowser()
    browser_web = invoker.get_command(Config.BROWSER)
    scrap_service = ScrapService(browser_web)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for user_service in users_service:
        data = {
            "browser": Config.BROWSER,
            "user_service": user_service,
            "service": service,
        }
        result = loop.run_until_complete(scrap_service.search(data))
        print(result)
    # Luego ejecutamos extract_data_task con el resultado de scrap_all_user_service_by_service_task
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


@c_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
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
                scrap_task.s(service["id"]),
            )
    except Exception as e:
        print(f"Error setting up periodic tasks: {e}")
    finally:
        loop.close()
