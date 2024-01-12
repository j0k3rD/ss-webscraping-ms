from flask import Flask
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    from app.resources.home_resource import home
    from app.resources.scrap_resource import scrapblue

    app.register_blueprint(home, url_prefix="/api/v1/")
    app.register_blueprint(scrapblue, url_prefix="/api/v1/")

    # url: str = os.getenv("SUPABASE_URL")
    # key: str = os.getenv("SUPABASE_KEY")
    # supabase: Client = create_client(url, key)

    # def get_user_data(user_id: str, property_id: str):
    #     result = (
    #         supabase.table("providers_ids")
    #         .select("*")
    #         .eq("user_id", user_id)
    #         .eq("property_id", property_id)
    #         .execute()
    #     )
    #     return result.data

    # user = get_user_data("3ec4ab3b-dc3e-4cb6-b5f9-fe52fd040a3f", "1")

    # print(user)

    return app
