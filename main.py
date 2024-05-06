from fastapi import FastAPI
from worker import scrap_task, extract_data_task
from celery import chain

description = """
SmartServices API helps you do awesome stuff. 🚀
"""

app = FastAPI(
    title="SmartService API - WEBSCRAPING MS",
    description=description,
    version="0.0.1",
)


@app.post("/scrap", tags=["scrap"])
async def scrap(data: dict):
    """
    Scrap data from a website.
    """
    scrap_tasks = scrap_task.delay(data)
    scrap_tasks.get()
    extract_tasks = extract_data_task.delay(data)

    return {
        "scrap_task_id": scrap_tasks.id,
        "extract_task_id": extract_tasks.id
    }
