from fastapi import FastAPI
from worker import scrap_task

description = """
SmartServices API helps you do awesome stuff. 🚀
"""

app = FastAPI(
    title="SmartService API - WEBSCRAPING MS",
    description=description,
    version="0.0.1",
)

@app.post("/scrap", tags=["scrap"])
def scrap_debt(data: dict):
    task = scrap_task.delay(data)
    return {"task_id": task.id}