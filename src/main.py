from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.workers.tasks import scrap_task

description = """
SmartServices API helps you do awesome stuff. 🚀
"""

app = FastAPI(
    root_path="/api/v1",
    title="SmartService API - WEBSCRAPING MS",
    description=description,
    version="0.0.1",
)

origins = [
    "http://0.0.0.0:5000",
    "http://localhost:5000",
    "http://ss-admin:5000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/scrap", tags=["scrap"])
async def scrap(data: dict):
    """
    Scrap data from a website.
    """
    scrap_task.delay(data)
    return {"status": "success"}
