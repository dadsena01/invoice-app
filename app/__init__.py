from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask
from flask_login import LoginManager
from app.models import db, User, initialize_db

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")
    app.config["SECRET_KEY"] = secret_key

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    from app.routes import api
    from app.auth import auth
    from app.views import views

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(views, url_prefix="/")
    initialize_db()
    return app
