import json
import smtplib
from email.message import EmailMessage
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from portal.extensions import db
from portal.models import Company, Notification, Role, Ticket, TicketUpdate, User


main_bp = Blueprint("main", __name__)

PERMISSION_CHOICES = [
    ("dashboard.view", "View dashboard"),
    ("tickets.view", "View tickets"),
    ("tickets.create", "Create tickets"),
    ("tickets.edit", "Edit tickets"),
    ("tickets.close", "Close tickets"),
    ("users.view", "View users"),
    ("users.create", "Create users"),
    ("users.edit", "Edit users"),
    ("users.disable", "Disable users"),
    ("roles.view", "View roles"),
    ("roles.create", "Create roles"),
    ("roles.edit", "Edit roles"),
    ("settings.view", "View settings"),
    ("settings.edit", "Edit settings"),
]
TABLE_PAGE_SIZE = 10


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please sign in to continue.", "info")
            return redirect(url_for("main.index"))
        return view(*args, **kwargs)

    return wrapped


def permission_required(permission):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please sign in to continue.", "info")
                return redirect(url_for("main.index"))
            permissions = json.loads(user.role.permissions or "[]")
            if permission not in permissions:
                flash("You do not have access to that section.", "error")
                return redirect(url_for("main.dashboard"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def tando_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not is_tando_admin(user):
            flash("You do not have access to that action.", "error")
            return redirect(url_for("main.dashboard"))
        return view(*args, **kwargs)

    return wrapped


def is_tando_admin(user):
    return bool(user and user.role.name == "admin" and user.company and user.company.code == "tando")


def scoped_query(query, user):
    return query if is_tando_admin(user) else query.filter_by(company_id=user.company_id)


def parent_company():
    return Company.query.filter_by(code="tando").first()


def paginate_query(query, page, per_page=TABLE_PAGE_SIZE):
    page = max(page, 1)
    per_page = max(per_page, 1)
    total = query.order_by(None).count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    total_pages = max((total + per_page - 1) // per_page, 1)
    has_prev = page > 1
    has_next = page < total_pages
    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next,
        "prev_page": page - 1 if has_prev else 1,
        "next_page": page + 1 if has_next else total_pages,
        "start_index": (page - 1) * per_page + 1 if total else 0,
    }


def render_app_page(template, **context):
    user = current_user()
    unread_notifications = 0
    recent_notifications = []
    if user:
        unread_notifications = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        recent_notifications = (
            Notification.query.filter_by(user_id=user.id)
            .order_by(Notification.created_at.desc())
            .limit(5)
            .all()
        )
    return render_template(
        template,
        current_user=user,
        current_permissions=json.loads(user.role.permissions or "[]") if user else [],
        is_tando_admin=is_tando_admin(user),
        unread_notifications=unread_notifications,
        recent_notifications=recent_notifications,
        **context,
    )


def send_notification_email(to_email, subject, body):
    from flask import current_app

    app = current_app._get_current_object()
    host = app.config.get("SMTP_HOST")
    if not host:
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = app.config.get("MAIL_FROM")
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(host, app.config.get("SMTP_PORT", 587), timeout=10) as smtp:
        if app.config.get("SMTP_USE_TLS", True):
            smtp.starttls()
        username = app.config.get("SMTP_USERNAME")
        password = app.config.get("SMTP_PASSWORD")
        if username:
            smtp.login(username, password)
        smtp.send_message(message)
    return True


def notify_user(user, title, message, ticket=None, notification_type="ticket_update", send_email=False):
    notification = Notification(
        user_id=user.id,
        ticket_id=ticket.id if ticket else None,
        title=title,
        message=message,
        notification_type=notification_type,
    )
    db.session.add(notification)
    if send_email:
        try:
            send_notification_email(user.email, title, message)
        except Exception:
            pass
    return notification


def parent_company_users():
    company = parent_company()
    if not company:
        return []
    return User.query.filter_by(company_id=company.id, is_active=True).all()


@main_bp.get("/")
def index():
    if current_user():
        return redirect(url_for("main.dashboard"))
    return render_app_page("login.html")


@main_bp.post("/login")
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        flash("Email and password are required.", "error")
        return render_app_page("login.html", email=email), 400
    user = User.query.filter_by(email=email, is_active=True).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("Invalid credentials. Please try again.", "error")
        return render_app_page("login.html", email=email), 401
    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.full_name
    flash("You have been signed in.", "success")
    return redirect(url_for("main.dashboard"))


@main_bp.get("/account/settings")
@login_required
def account_settings():
    user = current_user()
    return render_app_page(
        "account_settings.html",
        active_nav="account",
        user=user,
        user_email=user.email,
        user_name=user.full_name,
        password_min_length=6,
    )


@main_bp.post("/account/settings/name")
@login_required
def update_account_name():
    user = current_user()
    full_name = request.form.get("full_name", "").strip()
    if not full_name:
        flash("Name is required.", "error")
        return redirect(url_for("main.account_settings"))
    user.full_name = full_name
    db.session.commit()
    session["user_name"] = user.full_name
    flash("Name updated successfully.", "success")
    return redirect(url_for("main.account_settings"))


@main_bp.post("/account/settings/password")
@login_required
def update_account_password():
    user = current_user()
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    if not check_password_hash(user.password_hash, current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("main.account_settings"))
    if len(new_password) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect(url_for("main.account_settings"))
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash("Password updated successfully.", "success")
    return redirect(url_for("main.account_settings"))


@main_bp.get("/my-company")
@login_required
def my_company():
    user = current_user()
    company = user.company
    company_users_query = User.query.filter_by(company_id=company.id).order_by(User.created_at.desc()) if company else User.query.filter_by(id=None)
    page = request.args.get("page", 1, type=int)
    company_users_page = paginate_query(company_users_query, page)
    return render_app_page(
        "my_company.html",
        active_nav="company",
        user_email=user.email,
        user_name=user.full_name,
        company=company,
        company_users=company_users_page["items"],
        company_users_page=company_users_page,
    )


@main_bp.get("/contacts")
@login_required
def contacts():
    user = current_user()
    contacts_list = [
        {
            "name": "Business Development Manager",
            "person": "Allan Kipruto",
            "email": "allan@tando.co.ke",
            "phone": "+254 700 000 001",
            "role_note": "Client partnerships, escalations, and commercial follow-up.",
        },
        {
            "name": "Technical Officer",
            "person": "Technical Support",
            "email": "technical@tando.co.ke",
            "phone": "+254 700 000 002",
            "role_note": "Device setup, troubleshooting, and technical escalation.",
        },
        {
            "name": "Sales Officer",
            "person": "Sales Team",
            "email": "sales@tando.co.ke",
            "phone": "+254 700 000 003",
            "role_note": "Quotes, onboarding, and account growth support.",
        },
    ]
    return render_app_page(
        "contacts.html",
        active_nav="contacts",
        user_email=user.email,
        user_name=user.full_name,
        contacts_list=contacts_list,
    )


@main_bp.get("/reset-password")
def reset_password():
    return render_app_page("reset_password.html")


@main_bp.post("/reset-password")
def send_reset_password():
    email = request.form.get("email", "").strip().lower()
    if not email:
        flash("Please enter your email address.", "error")
        return render_app_page("reset_password.html", email=email), 400
    flash("If that email exists, a reset link will be sent shortly.", "success")
    return render_app_page("reset_password.html", email=email)


@main_bp.get("/dashboard")
@login_required
def dashboard():
    user = current_user()
    tickets_query = scoped_query(Ticket.query, user)
    is_parent = is_tando_admin(user)
    return render_app_page(
        "dashboard.html",
        active_nav="dashboard",
        user_email=user.email,
        user_name=user.full_name,
        company_count=Company.query.count() if is_parent else None,
        ticket_count=tickets_query.count() if is_parent else None,
        open_ticket_count=tickets_query.filter_by(status="open").count() if is_parent else None,
        closed_ticket_count=tickets_query.filter_by(status="closed").count() if is_parent else None,
        pending_ticket_count=tickets_query.filter_by(status="pending").count() if is_parent else None,
        user_count=scoped_query(User.query, user).count(),
        active_user_count=scoped_query(User.query, user).filter_by(is_active=True).count(),
        recent_tickets=tickets_query.order_by(Ticket.created_at.desc()).limit(5).all(),
        pending_my_action_count=tickets_query.filter_by(status="pending").count(),
        open_my_tickets_count=tickets_query.filter_by(status="open").count(),
        closed_my_tickets_count=tickets_query.filter_by(status="closed").count(),
        device_count=0 if is_parent else None,
        device_online_count=0 if is_parent else None,
        device_offline_count=0 if is_parent else None,
        visibility="all companies" if is_parent else "your company",
    )


@main_bp.get("/tickets")
@login_required
def tickets():
    user = current_user()
    tickets_query = scoped_query(Ticket.query, user)
    ticket_id = request.args.get("ticket_id", "").strip()
    status = request.args.get("status", "").strip()
    ticket_type = request.args.get("ticket_type", "").strip()
    product_group = request.args.get("product_group", "").strip()
    created_on = request.args.get("created_on", "").strip()
    company_id = request.args.get("company_id", "").strip() if is_tando_admin(user) else ""

    if ticket_id.isdigit():
        tickets_query = tickets_query.filter(Ticket.id == int(ticket_id))
    if status:
        tickets_query = tickets_query.filter(Ticket.status == status)
    if ticket_type:
        tickets_query = tickets_query.filter(Ticket.ticket_type == ticket_type)
    if product_group:
        tickets_query = tickets_query.filter(Ticket.serial_number.ilike(f"%{product_group}%"))
    if created_on:
        tickets_query = tickets_query.filter(db.func.date(Ticket.created_at) == created_on)
    if company_id and is_tando_admin(user):
        tickets_query = tickets_query.filter(Ticket.company_id == int(company_id))

    page = request.args.get("page", 1, type=int)
    tickets_page = paginate_query(tickets_query.order_by(Ticket.created_at.desc()), page)
    companies = Company.query.order_by(Company.name.asc()).all() if is_tando_admin(user) else Company.query.filter_by(id=user.company_id).all()
    return render_app_page(
        "tickets.html",
        active_nav="tickets",
        user_email=user.email,
        user_name=user.full_name,
        tickets_list=tickets_page["items"],
        tickets_page=tickets_page,
        companies=companies,
        can_view_all=is_tando_admin(user),
        filters={
            "ticket_id": ticket_id,
            "status": status,
            "ticket_type": ticket_type,
            "product_group": product_group,
            "created_on": created_on,
            "company_id": company_id,
        },
        ticket_type_labels={
            "issue_report": "Issue report",
            "service_request": "Service request",
            "technical_question": "Technical question",
            "product": "Product",
        },
    )


@main_bp.get("/tickets/new")
@login_required
def new_ticket():
    user = current_user()
    companies = Company.query.order_by(Company.name.asc()).all() if is_tando_admin(user) else Company.query.filter_by(id=user.company_id).all()
    return render_app_page(
        "tickets_new.html",
        active_nav="tickets",
        user_email=user.email,
        user_name=user.full_name,
        companies=companies,
        can_view_all=is_tando_admin(user),
        ticket_company_required=is_tando_admin(user),
    )


@main_bp.get("/users")
@login_required
@permission_required("users.view")
def users():
    user = current_user()
    users_query = User.query.order_by(User.created_at.desc())
    if not is_tando_admin(user):
        users_query = users_query.filter_by(company_id=user.company_id)
    page = request.args.get("page", 1, type=int)
    users_page = paginate_query(users_query, page)
    companies = Company.query.order_by(Company.name.asc()).all() if is_tando_admin(user) else Company.query.filter_by(id=user.company_id).all()
    roles = Role.query.order_by(Role.name.asc()).all()
    return render_app_page(
        "users.html",
        active_nav="users",
        user_email=user.email,
        user_name=user.full_name,
        users_list=users_page["items"],
        users_page=users_page,
        companies=companies,
        roles=roles,
        can_use_parent_company=is_tando_admin(user),
    )


@main_bp.post("/users")
@login_required
@permission_required("users.create")
def create_user():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()
    role_id = request.form.get("role_id", "").strip()
    company_id = request.form.get("company_id", "").strip()
    if not all([full_name, email, password, role_id, company_id]):
        flash("All user fields are required.", "error")
        return redirect(url_for("main.users"))
    if len(password) < 6:
        flash("Password must be at least 6 characters.", "error")
        return redirect(url_for("main.users"))
    if User.query.filter_by(email=email).first():
        flash("That email is already in use.", "error")
        return redirect(url_for("main.users"))
    role = db.session.get(Role, int(role_id))
    company = parent_company() if company_id == "0" else db.session.get(Company, int(company_id))
    if not role:
        flash("Selected role does not exist.", "error")
        return redirect(url_for("main.users"))
    if not company:
        flash("Selected company does not exist.", "error")
        return redirect(url_for("main.users"))
    user = User(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
        company_id=company.id,
        role_id=role.id,
    )
    db.session.add(user)
    db.session.commit()
    flash("User created successfully.", "success")
    return redirect(url_for("main.users"))


@main_bp.post("/users/<int:user_id>/edit")
@login_required
@permission_required("users.edit")
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("main.users"))

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    role_id = request.form.get("role_id", "").strip()
    company_id = request.form.get("company_id", "").strip()

    if full_name:
        user.full_name = full_name
    if email and email != user.email:
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            flash("That email is already in use.", "error")
            return redirect(url_for("main.users"))
        user.email = email

    if role_id:
        role = db.session.get(Role, int(role_id))
        if role:
            user.role_id = role.id

    if company_id:
        company = parent_company() if company_id == "0" else db.session.get(Company, int(company_id))
        if company:
            user.company_id = company.id

    db.session.commit()
    flash("User updated successfully.", "success")
    return redirect(url_for("main.users"))


@main_bp.post("/users/<int:user_id>/toggle")
@login_required
@permission_required("users.disable")
def toggle_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("main.users"))
    if current_user().id == user.id:
        flash("You cannot disable your own account.", "error")
        return redirect(url_for("main.users"))
    user.is_active = not user.is_active
    db.session.commit()
    flash("User status updated successfully.", "success")
    return redirect(url_for("main.users"))


@main_bp.get("/roles")
@login_required
@permission_required("roles.view")
def roles_page():
    user = current_user()
    page = request.args.get("page", 1, type=int)
    roles_page = paginate_query(Role.query.order_by(Role.created_at.desc()), page)
    return render_app_page(
        "roles.html",
        active_nav="roles",
        user_email=user.email,
        user_name=user.full_name,
        roles_list=roles_page["items"],
        roles_page=roles_page,
        permission_choices=PERMISSION_CHOICES,
    )


@main_bp.post("/roles")
@login_required
@tando_admin_required
def create_role():
    name = request.form.get("name", "").strip().lower()
    description = request.form.get("description", "").strip()
    permissions = request.form.getlist("permissions")
    if not name:
        flash("Role name is required.", "error")
        return redirect(url_for("main.roles_page"))
    if Role.query.filter_by(name=name).first():
        flash("Role already exists.", "error")
        return redirect(url_for("main.roles_page"))
    role = Role(name=name, description=description or None, permissions=json.dumps(permissions))
    db.session.add(role)
    db.session.commit()
    flash("Role created successfully.", "success")
    return redirect(url_for("main.roles_page"))


@main_bp.post("/roles/<int:role_id>")
@login_required
@tando_admin_required
def update_role(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        flash("Role not found.", "error")
        return redirect(url_for("main.roles_page"))

    role.description = request.form.get("description", "").strip() or None
    role.permissions = json.dumps(request.form.getlist("permissions"))
    db.session.commit()
    flash("Role updated successfully.", "success")
    return redirect(url_for("main.roles_page"))


@main_bp.post("/roles/<int:role_id>/delete")
@login_required
@tando_admin_required
def delete_role(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        flash("Role not found.", "error")
        return redirect(url_for("main.roles_page"))
    if role.name == "admin":
        flash("The admin role cannot be deleted.", "error")
        return redirect(url_for("main.roles_page"))
    db.session.delete(role)
    db.session.commit()
    flash("Role deleted successfully.", "success")
    return redirect(url_for("main.roles_page"))


@main_bp.get("/companies")
@login_required
@tando_admin_required
def companies():
    user = current_user()
    page = request.args.get("page", 1, type=int)
    companies_page = paginate_query(Company.query.order_by(Company.created_at.desc()), page)
    roles = Role.query.order_by(Role.name.asc()).all()
    return render_app_page(
        "companies.html",
        active_nav="companies",
        user_email=user.email,
        user_name=user.full_name,
        companies_list=companies_page["items"],
        companies_page=companies_page,
        roles=roles,
    )


@main_bp.post("/companies")
@login_required
@tando_admin_required
def create_company():
    company_name = request.form.get("company_name", "").strip()
    company_code = request.form.get("company_code", "").strip().lower()
    admin_name = request.form.get("admin_name", "").strip()
    admin_email = request.form.get("admin_email", "").strip().lower()
    admin_password = request.form.get("admin_password", "").strip()
    admin_role_id = request.form.get("admin_role_id", "").strip()

    if not all([company_name, company_code, admin_name, admin_email, admin_password, admin_role_id]):
        flash("Company and admin details are required.", "error")
        return redirect(url_for("main.companies"))
    if len(admin_password) < 6:
        flash("Admin password must be at least 6 characters.", "error")
        return redirect(url_for("main.companies"))

    if Company.query.filter((Company.name == company_name) | (Company.code == company_code)).first():
        flash("Company name or code already exists.", "error")
        return redirect(url_for("main.companies"))

    if User.query.filter_by(email=admin_email).first():
        flash("That admin email is already in use.", "error")
        return redirect(url_for("main.companies"))

    role = db.session.get(Role, int(admin_role_id))
    if not role:
        flash("Selected admin role does not exist.", "error")
        return redirect(url_for("main.companies"))

    company = Company(name=company_name, code=company_code, contact_email=admin_email or None)
    db.session.add(company)
    db.session.flush()

    admin_user = User(
        full_name=admin_name,
        email=admin_email,
        password_hash=generate_password_hash(admin_password),
        company_id=company.id,
        role_id=role.id,
    )
    db.session.add(admin_user)
    db.session.commit()
    flash("Company and primary admin created successfully.", "success")
    return redirect(url_for("main.companies"))


@main_bp.post("/companies/<int:company_id>/toggle")
@login_required
@tando_admin_required
def toggle_company(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        flash("Company not found.", "error")
        return redirect(url_for("main.companies"))
    company.is_active = not company.is_active
    db.session.commit()
    flash("Company status updated successfully.", "success")
    return redirect(url_for("main.companies"))


@main_bp.post("/tickets")
@login_required
@permission_required("tickets.create")
def create_ticket():
    user = current_user()
    title = request.form.get("title", "").strip()
    ticket_type = request.form.get("ticket_type", "").strip()
    serial_number = request.form.get("serial_number", "").strip()
    description = request.form.get("description", "").strip()
    company_id = request.form.get("company_id", "").strip() if is_tando_admin(user) else str(user.company_id or "")
    if not title or not ticket_type or not company_id:
        flash("Ticket title and type are required.", "error")
        return redirect(url_for("main.new_ticket"))
    company = parent_company() if company_id == "0" else db.session.get(Company, int(company_id))
    if not company:
        flash("Selected company does not exist.", "error")
        return redirect(url_for("main.new_ticket"))
    if not is_tando_admin(user) and user.company_id != company.id:
        flash("You can only create tickets for your own company.", "error")
        return redirect(url_for("main.new_ticket"))
    if ticket_type == "product" and not serial_number:
        flash("Serial number is required for product tickets.", "error")
        return redirect(url_for("main.new_ticket"))
    ticket = Ticket(
        title=title,
        ticket_type=ticket_type,
        serial_number=serial_number or None,
        description=description or None,
        company_id=company.id,
        created_by_id=user.id,
        status="open",
    )
    db.session.add(ticket)
    db.session.flush()

    if company.code == "tando":
        recipients = User.query.filter_by(company_id=company.id, is_active=True).all()
    else:
        recipients = parent_company_users()
    parent = parent_company()

    notification_title = f"New ticket: {ticket.title}"
    notification_message = f"{user.full_name} created a {ticket_type.replace('_', ' ')} ticket for {company.name}."
    for recipient in recipients:
        notify_user(
            recipient,
            notification_title,
            notification_message,
            ticket=ticket,
            notification_type="ticket_created",
            send_email=bool(parent and recipient.company_id == parent.id),
        )

    db.session.commit()
    flash("Ticket created successfully.", "success")
    return redirect(url_for("main.tickets"))


@main_bp.post("/tickets/<int:ticket_id>/respond")
@login_required
@permission_required("tickets.edit")
def respond_to_ticket(ticket_id):
    user = current_user()
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        flash("Ticket not found.", "error")
        return redirect(url_for("main.tickets"))
    if not is_tando_admin(user):
        flash("You do not have access to that action.", "error")
        return redirect(url_for("main.tickets"))

    message = request.form.get("message", "").strip()
    new_status = request.form.get("status", "").strip() or ticket.status
    if not message:
        flash("Response message is required.", "error")
        return redirect(url_for("main.tickets"))

    ticket.status = new_status
    update = TicketUpdate(ticket_id=ticket.id, author_id=user.id, message=message)
    db.session.add(update)
    notify_user(
        ticket.created_by,
        f"Update on ticket: {ticket.title}",
        message,
        ticket=ticket,
        notification_type="ticket_update",
        send_email=False,
    )
    db.session.commit()
    flash("Ticket response sent.", "success")
    return redirect(url_for("main.tickets"))


@main_bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("main.index"))


@main_bp.post("/notifications/<int:notification_id>/read")
@login_required
def read_notification(notification_id):
    user = current_user()
    notification = db.session.get(Notification, notification_id)
    if notification and notification.user_id == user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(request.referrer or url_for("main.dashboard"))
