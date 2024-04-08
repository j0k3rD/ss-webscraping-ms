from flask import Flask
from dotenv import load_dotenv
import os
from flask_wtf import CSRFProtect


load_dotenv()


def create_app():
    app = Flask(__name__)
    csrf = CSRFProtect()
    csrf.init_app(app)  # Compliant

    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

    from app.resources.home_resource import home
    from app.resources.scrap_resource import scrapblue

    app.register_blueprint(home, url_prefix="/api/v1/")
    app.register_blueprint(scrapblue, url_prefix="/api/v1/")

    return app
