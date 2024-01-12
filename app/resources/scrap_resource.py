from flask import Blueprint, jsonify
from app import tasks
import os
from supabase import create_client, Client
from celery.result import AsyncResult

scrapblue = Blueprint("scrapblue", __name__, url_prefix="/")


@scrapblue.route("/search/<browser>/<clientid>/<propertyid>/", methods=["GET"])
def search(browser, clientid, propertyid):
    """
    Funcion llamada por request GET a la ruta /api/v1/search/<browser>/<propertyid>/<clientid>/

    args:
        - browser: Indica el navegador a utilizar para la busqueda
        - propertyid: Indica el id de la propiedad
        - clientid: Indica el id del cliente del proveedor de servicios
    return:
        - resp: Deuda si / no
    """
    # Iniciar la tarea asincrónica
    task = tasks.scrap_task.delay(browser, propertyid, clientid)

    # Obtener el ID de la tarea
    task_id = task.id

    # Esperar hasta que la tarea se complete
    task_result = AsyncResult(task_id).get()

    # Comprobar el resultado y devolver una respuesta JSON
    if task_result:
        return jsonify({"deuda": "si"})
    else:
        return jsonify({"deuda": "no"})
