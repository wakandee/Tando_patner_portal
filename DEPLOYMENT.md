# Deployment Guide

This project is a Flask app intended to run behind Passenger with MySQL.

## Files To Upload

Upload these project files and folders to the server:

- `app.py`
- `passenger_wsgi.py`
- `portal/`
- `migrations/`
- `templates/`
- `static/`
- `requirements.txt`
- `.env` on the server only

## Files To Leave Out

Do not upload these from your local machine:

- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.env.example`
- local SQLite or database files
- editor and OS temporary files

## Environment Variables

Set the MySQL values in `.env`:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_EXTRA`

`DATABASE_URL` is still supported if you want to provide a single connection string instead.

## Passenger Entry Point

Passenger should point at `passenger_wsgi.py`, which exposes the Flask app as `application`.

## Go-Live Steps

1. Upload the project files.
2. Create the `.env` file on the server.
3. Install dependencies with `pip install -r requirements.txt`.
4. Run database migrations with `flask db upgrade`.
5. Seed the initial data if needed with `flask seed-data`.
6. Restart Passenger or your web server.

## Notes

- Keep `SECRET_KEY` strong and unique in production.
- Set `INITIAL_ADMIN_PASSWORD` to a temporary value, then change it after first login.
- Make sure your server MySQL user has permissions for the application database.
