from flask import Blueprint, jsonify
from app import tasks
from celery.result import AsyncResult

scrapblue = Blueprint("scrapblue", __name__, url_prefix="/")


@scrapblue.route(
    "/search/<browser>/<clientid>/<propertyid>/<service>/", methods=["GET"]
)
def search_by_service(browser, clientid, propertyid, service):
    """
    Funcion llamada por request GET a la ruta /api/v1/search/<browser>/<clientid>/<propertyid>/<service>/

    args:
        - browser: Indica el navegador a utilizar para la busqueda
        - clientid: Indica el id del cliente del proveedor de servicios
        - propertyid: Indica el id de la propiedad del cliente
        - service: Indica el servicio a buscar
    return:
        - resp: Deuda si / no
    """
    # Iniciar la tarea asincrónica
    task = tasks.scrap_by_service.delay(browser, clientid, propertyid, service)

    # Obtener el ID de la tarea
    task_id = task.id

    # Esperar hasta que la tarea se complete
    task_result = AsyncResult(task_id).get()

    # Comprobar el resultado y devolver una respuesta JSON
    if task_result:
        return jsonify({"deuda": "si"})
    else:
        return jsonify({"deuda": "no"})


@scrapblue.route("/search/<browser>/<clientid>/<propertyid>", methods=["GET"])
def search_all(browser, clientid, propertyid):
    """
    Funcion llamada por request GET a la ruta /api/v1/search/<browser>/<clientid>/<propertyid>/

    args:
        - browser: Indica el navegador a utilizar para la busqueda
        - clientid: Indica el id del cliente del proveedor de servicios
        - propertyid: Indica el id de la propiedad del cliente
    return:
        - resp: Deuda si / no
    """
    # Iniciar la tarea asincrónica
    task = tasks.scrap_all.delay(browser, clientid, propertyid)

    # Obtener el ID de la tarea
    task_id = task.id

    # Esperar hasta que la tarea se complete
    task_result = AsyncResult(task_id).get()

    # Comprobar el resultado y devolver una respuesta JSON
    if task_result:
        return jsonify({"deuda": "si"})
    else:
        return jsonify({"deuda": "no"})
