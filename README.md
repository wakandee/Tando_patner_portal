# TANDO Partner Portal

TANDO Partner Portal is a Flask-based internal portal for managing partner accounts, companies, roles, tickets, and basic account settings for TANDO IoT AI camera clients.

## Overview

The application is structured as a modular Flask package so the core concerns stay separated:

- `app.py` is the application entry point
- `portal/` contains the application package, configuration, models, routes, and seed logic
- `migrations/` stores database migration files
- `templates/` and `static/` contain the UI templates and assets

## Project Structure

```text
Patner_portal/
|- app.py
|- .env
|- .env.example
|- portal/
|  |- __init__.py
|  |- config.py
|  |- extensions.py
|  |- models.py
|  |- routes.py
|  `- seed.py
|- migrations/
|- static/
|  `- css/
|     `- main.css
`- templates/
   |- account_settings.html
   |- base.html
   |- companies.html
   |- dashboard.html
   |- icons/
   |- login.html
   |- my_company.html
   |- reset_password.html
   |- roles.html
   |- tickets.html
   `- users.html
```

## Requirements

- Python 3.13 or compatible
- MySQL
- A virtual environment is recommended for local development

## Fresh Install

Follow these steps for a clean local setup.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run this first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create the database

Create a MySQL database named:

```sql
tando_patner_portal
```

The application reads its database connection from `DATABASE_URL` in `.env`.

### 4. Configure environment variables

Copy `.env.example` to `.env` and update the values for your local MySQL setup.

### 5. Initialize the schema

```powershell
flask init-db
```

### 6. Seed the initial data

```powershell
flask seed-data
```

This seeding step creates the initial Tando company, the admin role, and the default admin user defined in [`portal/seed.py`](/D:/KINDE/Tando/Patner_portal/portal/seed.py).

### 7. Start the application

```powershell
python app.py
```

Open the application at:

```text
http://127.0.0.1:5000
```

## Configuration

The main application settings are defined in [`portal/config.py`](/D:/KINDE/Tando/Patner_portal/portal/config.py).

Important environment variables:

- `SECRET_KEY`
- `DATABASE_URL`
- `INITIAL_ADMIN_NAME`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`

## Default Seeded Admin

- Email: `admin@tando.co.ke`
- Password: `ChangeMe123!`

## Notes

- The app is configured for MySQL by default.
- Generated SQLite files and the `instance/` directory are ignored and should not be committed.
- The `seed-data` CLI command is registered in [`portal/__init__.py`](/D:/KINDE/Tando/Patner_portal/portal/__init__.py).
- Role-based access control is implemented through roles and permissions.
- The portal is structured to make future modules such as `users`, `tickets`, `rma`, and `settings` easy to add.
