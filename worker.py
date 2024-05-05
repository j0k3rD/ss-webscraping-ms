import os, asyncio
from celery import Celery
from src.utils.browser_invoker import InvokerBrowser
from src.services.scrap_service import ScrapService


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


@celery.task
def scrap_task(data: dict):
    invoker = InvokerBrowser()
    browser_data = data['browser']
    browser = browser_data.lower()
    browser_web = invoker.get_command(browser)
    scrap_service = ScrapService(browser_web)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrap_service.search(data))
    print(result)
    return result