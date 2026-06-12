import logging

from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
from pathlib import Path
import json

from portal.config import configure_app
from portal.extensions import db
from portal.routes import main_bp
from portal.seed import seed_initial_data


def create_app():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    configure_app(app)
    db.init_app(app)
    Migrate(app, db)
    app.register_blueprint(main_bp)
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.propagate = False

    @app.template_filter("loads_json")
    def loads_json(value):
        try:
            return json.loads(value or "[]")
        except json.JSONDecodeError:
            return []

    @app.cli.command("init-db")
    def init_db_command():
        """Create all tables in the configured database."""
        with app.app_context():
            db.create_all()
        print("Database initialized.")

    @app.cli.command("seed-data")
    def seed_data_command():
        """Seed the initial admin role and user."""
        with app.app_context():
            seed_initial_data(app)
        print("Initial data seeded.")

    return app
