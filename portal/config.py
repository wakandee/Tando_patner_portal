import os
from urllib.parse import quote_plus


def _build_database_uri():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "tando_patner_portal")
    db_extra = os.getenv("DB_EXTRA", "")

    credentials = quote_plus(db_user)
    if db_password:
        credentials = f"{credentials}:{quote_plus(db_password)}"

    uri = f"mysql+pymysql://{credentials}@{db_host}:{db_port}/{db_name}"
    if db_extra:
        separator = "&" if "?" in uri else "?"
        uri = f"{uri}{separator}{db_extra.lstrip('?&')}"
    return uri


def configure_app(app):
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["DEBUG"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = _build_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["INITIAL_ADMIN_NAME"] = os.getenv("INITIAL_ADMIN_NAME", "Tando Admin")
    app.config["INITIAL_ADMIN_EMAIL"] = os.getenv("INITIAL_ADMIN_EMAIL", "admin@tando.co.ke")
    app.config["INITIAL_ADMIN_PASSWORD"] = os.getenv("INITIAL_ADMIN_PASSWORD", "ChangeMe123!")
    app.config["SMTP_HOST"] = os.getenv("SMTP_HOST", "")
    app.config["SMTP_PORT"] = int(os.getenv("SMTP_PORT", "587"))
    app.config["SMTP_USERNAME"] = os.getenv("SMTP_USERNAME", "")
    app.config["SMTP_PASSWORD"] = os.getenv("SMTP_PASSWORD", "")
    app.config["SMTP_USE_TLS"] = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}
    app.config["MAIL_FROM"] = os.getenv("MAIL_FROM", "no-reply@tando.co.ke")
