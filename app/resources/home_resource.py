from flask import Blueprint, jsonify
import redis


home = Blueprint("home", __name__, url_prefix="/")


@home.route("/", methods=["GET"])
def index():
    """
    Funcion llamada por request GET a la ruta /api/v1/

    return:
        - json: Devuelve un json con el nombre del proyecto
    """
    resp = jsonify({"project": "Web Scraping Microservice"})
    resp.status_code = 200
    return resp


@home.route("/healthcheck", methods=["GET"])
def health_check():
    """
    Función que chequea el estado del servidor de redis
    """
    # Checkemos el Redis
    redis_host = "redis"
    redis_port = 6379

    try:
        r = redis.Redis(
            host=redis_host, port=redis_port, socket_connect_timeout=1, socket_timeout=1
        )
        r.ping()
        redis_status = 200
    except redis.exceptions.ConnectionError:
        redis_status = 500

    data = {
        "redis": redis_status,
    }

    resp = jsonify(data)
    resp.status_code = 200
    return resp
