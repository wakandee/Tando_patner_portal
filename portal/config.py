import os


def configure_app(app):
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@127.0.0.1:3306/tando_patner_portal",
    )
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
