"""WSGI entrypoint for production servers (gunicorn on Railway).

Importing this module:
- constructs the Flask app
- runs ``init_db()`` (CREATE TABLE IF NOT EXISTS, safe to repeat)
- runs ``seed_db()`` (no-op when users already exist, safe to repeat)

Gunicorn command (see Procfile):
    gunicorn --bind 0.0.0.0:$PORT wsgi:app
"""

from app import app  # noqa: F401  (gunicorn imports `app` from this module)
from database.db import init_db, seed_db


# Ensure the schema and demo data exist before the first request is served.
# On a fresh volume this creates the demo user so the login page is usable
# the moment the URL loads. On subsequent boots both calls are no-ops.
init_db()
seed_db()
