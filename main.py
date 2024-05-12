from fastapi import FastAPI
from worker import scrap_task, setup_periodic_tasks
from datetime import datetime

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
    scrap_task.delay(data)
    return {"status": "success"}