import asyncio
import importlib
import logging

from typing import Any, Dict
from celery import Celery
from celery.schedules import crontab
from celery.contrib.abortable import AbortableTask
import ast

from src.core.errors import WebScrapingError
from src.core.logging_config import setup_logging
from src.utils.browser_invoker import InvokerBrowser
from src.services.web_scrap_service import WebScrapService
from src.services.extract_data_service import ExtractDataService
from src.core.config import Config
from src.services.http_client import MainServiceClient

client = MainServiceClient()
c_app = Celery()
c_app.config_from_object("src.core.config")


def async_task(f):
    def wrapper(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(self, *args, **kwargs))
        finally:
            loop.close()

    return wrapper


@c_app.task(bind=True, base=AbortableTask)
def scrap_task(self, data: Dict[str, Any]) -> Dict[str, Any]:

    @async_task
    async def _scrap_task(data: Dict[str, Any]) -> Dict[str, Any]:

        logger = logging.getLogger("scraping_task")

        scrap_service = WebScrapService()
        extract_service = ExtractDataService()

        # try:
        #     async with WebScrapService() as scrap_service:
        #         result = await scrap_service.search(data)
        #         logger.info("Scraping completed successfully")

        #         if result.get("should_extract", True):
        #             try:
        extract_service = ExtractDataService()
        await extract_service.process_bills(data)
        return {
            "status": "success",
            "message": "Data extracted successfully",
        }
        #     except Exception as e:
        #         logger.error(f"Extraction failed: {str(e)}")
        #         return {
        #             "status": "error",
        #             "message": f"Error during extraction: {str(e)}",
        #         }
        # else:
        #     return {
        #         "status": "success",
        #         "message": result.get("save_result", {}).get(
        #             "message", "No action needed"
        #         ),
        #     }

        # except Exception as e:
        #     logger.error(f"Unexpected error: {str(e)}")
        #     return {"status": "error", "message": str(e)}

    return _scrap_task(data)


@c_app.task(bind=True, base=AbortableTask)
def scrap_all_user_service_by_service_task(self, service):
    """Wrapper task for async scraping of all user services"""

    @async_task
    async def _scrap_all_task(service):
        service_id = service["id"]
        users_service = await client.get_user_services_by_service(service_id)

        if users_service == "No user_service found":
            return {"error": "No user_service found"}

        invoker = InvokerBrowser()
        browser_web = invoker.get_command(Config.BROWSER)
        scrap_service = WebScrapService()

        final_result = None
        for user_service in users_service:
            data = {
                "browser": Config.BROWSER,
                "user_service": user_service,
                "service": service,
            }
            result = await scrap_service.search(data)
            final_result = result

        if final_result and final_result[1] != "No new bills to save":
            try:
                extract_service = ExtractDataService()
                await extract_service.process_bills(data)
                return {"status": "success"}
            except Exception as e:
                return {"error": f"Error: {e}"}
        else:
            return {"status": "success"}

    return _scrap_all_task(service)


# @c_app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     """Set up periodic tasks for web scraping"""

#     async def _setup_tasks():
#         try:
#             services = await client.get_services()
#             for service in services:
#                 crondict = ast.literal_eval(service["crontab"])
#                 sender.add_periodic_task(
#                     crontab(
#                         minute=str(list(crondict["minute"])[0]),
#                         hour=str(list(crondict["hour"])[0]),
#                         day_of_week=",".join(map(str, crondict["day_of_week"])),
#                         day_of_month=",".join(map(str, crondict["day_of_month"])),
#                         month_of_year=",".join(map(str, crondict["month_of_year"])),
#                     ),
#                     scrap_task.s(service),
#                 )
#         except Exception as e:
#             print(f"Error setting up periodic tasks: {e}")

#     # Use a proper async event loop integration
#     loop = asyncio.get_event_loop()
#     loop.create_task(_setup_tasks())
