import json

from werkzeug.security import generate_password_hash

from portal.extensions import db
from portal.models import Company, Role, User


ALL_PERMISSIONS = [
    "dashboard.view",
    "tickets.view",
    "tickets.create",
    "tickets.edit",
    "tickets.close",
    "users.view",
    "users.create",
    "users.edit",
    "users.disable",
    "roles.view",
    "roles.create",
    "roles.edit",
    "settings.view",
    "settings.edit",
]


def seed_initial_data(app):
    db.create_all()

    tando_company = Company.query.filter_by(code="tando").first()
    if not tando_company:
        tando_company = Company(
            name="Tando",
            code="tando",
            contact_email=app.config["INITIAL_ADMIN_EMAIL"],
        )
        db.session.add(tando_company)
        db.session.flush()

    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(
            name="admin",
            description="Full access administrator",
            permissions=json.dumps(ALL_PERMISSIONS),
        )
        db.session.add(admin_role)
        db.session.flush()
    else:
        admin_role.description = "Full access administrator"
        admin_role.permissions = json.dumps(ALL_PERMISSIONS)

    admin_email = app.config["INITIAL_ADMIN_EMAIL"]
    admin_user = User.query.filter_by(email=admin_email).first()

    if not admin_user:
        admin_user = User(
            full_name=app.config["INITIAL_ADMIN_NAME"],
            email=admin_email,
            password_hash=generate_password_hash(app.config["INITIAL_ADMIN_PASSWORD"]),
            company_id=tando_company.id,
            role_id=admin_role.id,
        )
        db.session.add(admin_user)
    else:
        admin_user.full_name = app.config["INITIAL_ADMIN_NAME"]
        admin_user.company_id = tando_company.id
        admin_user.role_id = admin_role.id

    db.session.commit()
