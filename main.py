from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Depends

from worker import scrap_task
from src.utils.browser_invoker import InvokerBrowser
from src.services.scrap_service import ScrapService

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

app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# @app.get("/")
# def home(request: Request):
#     return templates.TemplateResponse("home.html", context={"request": request})


# @app.post("/tasks", status_code=201)
# def run_task(payload = Body(...)):
#     task_type = payload["type"]
#     task = create_task.delay(int(task_type))
#     return JSONResponse({"task_id": task.id})


# @app.get("/tasks/{task_id}")
# def get_status(task_id):
#     task_result = AsyncResult(task_id)
#     result = {
#         "task_id": task_id,
#         "task_status": task_result.status,
#         "task_result": task_result.result
#     }
#     return JSONResponse(result)