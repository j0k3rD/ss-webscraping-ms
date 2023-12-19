# app/__init__.py
from flask import Flask
from ..config import SECRET_KEY

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY

    from .resources.routes import web_scraping_bp
    app.register_blueprint(web_scraping_bp, url_prefix='/web_scraping')

    return app