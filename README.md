# Spendly

A small Flask expense tracker — log expenses by category, see monthly and
per-category totals on a dashboard, filter by date. Originally deployed on
Railway; this repo also ships with a Render Blueprint for the free web
service tier.

## Deploying to Render (free tier)

1. Push this repo to GitHub.
2. In the Render dashboard, click **New + → Blueprint**.
3. Point Render at your fork. It will detect `render.yaml` and create the
   service. Render auto-generates `SECRET_KEY` at create-time; everything
   else comes from the Blueprint.
4. Wait for the first build. The default URL ends in `onrender.com`.
5. Open the URL → click **Sign in** → log in with the seeded demo user:
   - Email: `demo@spendly.com`
   - Password: `demo123`
6. (Optional) Register your own account.

### Free-tier caveats

Render's free web service **spins down after 15 minutes of inactivity**, and
the first request after a cold start takes ~30 seconds. This is normal.

More importantly, **SQLite on Render free is ephemeral**: the database file
lives on the container's disk, so it is wiped on every redeploy *and* on
every cold-start. The demo user is recreated automatically by `seed_db()` on
boot (so the seeded login keeps working), but any account you registered
yourself is lost between deploys.

If you need data to survive redeploys, either upgrade to a Render paid plan
and attach a persistent disk (`DATABASE_PATH=/data/spendly.db`), or migrate
to a managed Postgres database (Render, Neon, Supabase all have free tiers).

## Local development

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5001.

## How this is wired for production

- `app.py` reads `SECRET_KEY` from the environment (falls back to a dev-only
  default for local runs).
- `database/db.py` reads `DATABASE_PATH` from the environment; default is
  `spendly.db` in the working directory.
- `wsgi.py` constructs the Flask app and runs `init_db()` + `seed_db()`
  once at import, so a fresh deployment always has the schema and demo
  user in place before the first request.
- `Procfile` and `render.yaml` both start gunicorn with
  `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 60 wsgi:app`.
- `runtime.txt` pins Python 3.11.
- `railway.json` is left in place for the original Railway deploy path; it
  is ignored by Render.

## Tests

```bash
pytest
```

The repo's test suite lives in `tests/`.