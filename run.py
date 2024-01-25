from app import create_app
import os

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host=os.getenv("HOST"), port=os.getenv("PORT"))
