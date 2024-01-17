from flask import Flask
from flask_migrate import Migrate
from flask_pydantic_spec import FlaskPydanticSpec
from flask_sqlalchemy import SQLAlchemy

from .config import config

db = SQLAlchemy()
migrate = Migrate()

spec = FlaskPydanticSpec("flask", title="API: Mata-Mata", version="v1")


def create_app(config_mode):
    app = Flask(__name__)
    app.config.from_object(config[config_mode])
    db.init_app(app)
    migrate.init_app(app, db)
    spec.register(app)

    from .urls import api_blueprint

    app.register_blueprint(api_blueprint)
    with app.app_context():
        db.create_all()

    return app
