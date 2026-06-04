# Ledger

Internal audit planning dashboard. Tracks engagements, allocates team hours
over a 52-week horizon, and exports Excel workbooks for the Audit Committee.

Streamlit + SQLAlchemy + openpyxl. SQLite by default, swap in PostgreSQL via
`DATABASE_URL`. Runs locally, in Docker, or as a Databricks App.

## Run locally

```bash
git clone https://github.com/josephdmcdevitt-svg/audit-dashboard.git
cd audit-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501.

First start creates `data/workspace.db` and seeds 4 sample audits and a
6-person team. If no `auth_config.yaml` exists, set `BOOTSTRAP_ADMIN_PASSWORD`
to a strong password before the first run; the app creates an `admin` user
from it. Add more users by generating hashes:

```bash
python -m auth --hash YOUR_NEW_PASSWORD
# paste the hash into auth_config.yaml
```

## Deploy to Databricks Apps

The repo includes an `app.yaml`, which is all Databricks Apps needs (the
Dockerfile is for other hosts; Databricks ignores it and installs
`requirements.txt` into its own runtime, Python 3.11 on Ubuntu 22.04).

1. Sync the repo into your workspace (Git folder or `databricks apps deploy`).
2. Edit `app.yaml`: set `EDITOR_EMAILS` to the comma-separated workspace
   emails that should get edit rights. Everyone else is a viewer.
3. Point `DATABASE_URL` at Postgres (Lakebase or any reachable instance),
   ideally via a secret resource. The app container filesystem is ephemeral,
   so the default SQLite file is wiped on every redeploy or restart.
4. Deploy. Do not set ports or addresses; the runtime injects
   `STREAMLIT_SERVER_PORT` and `STREAMLIT_SERVER_ADDRESS` automatically.

On Databricks there is no login form. The app reads the SSO identity that
Databricks forwards in request headers (`X-Forwarded-Email`) and maps the
role from `EDITOR_EMAILS`. The streamlit-authenticator flow only runs for
local and Docker deployments. To preview the SSO path locally, set
`DEV_FAKE_USER_EMAIL=you@example.com`.

## Tests

```bash
pip install pytest
python -m pytest tests/
```

## Users and roles

`auth_config.yaml` controls who can sign in. Each user has a name, email,
bcrypt password hash, and one role:

- `editor` - full access (Dashboard, Audit Plan, Team, Executive, Activity, Export)
- `viewer` - read-only (Dashboard, Executive)

Generate a fresh cookie key when you set up the file:

```bash
python -c "import bcrypt; print(bcrypt.gensalt().decode())"
```

## Deploy

The app runs as a single container on port 8501. Anywhere that hosts a
container will work: corporate Kubernetes, an internal Docker host, a Linux
VM with Docker installed.

```bash
docker build -t ledger:latest .
docker run -d \
  -p 8501:8501 \
  -v /srv/ledger/data:/app/data \
  -v /srv/ledger/auth_config.yaml:/app/auth_config.yaml:ro \
  -e DATABASE_URL="sqlite:///data/workspace.db" \
  --name ledger ledger:latest
```

Mount `data/` and `auth_config.yaml` from the host so the database and user
config survive container restarts.

For a host without Docker, see `deploy/startup.sh` - it installs deps and
starts Streamlit with the same flags.

## PostgreSQL

For multi-user editing, point `DATABASE_URL` at PostgreSQL:

```
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/ledger?sslmode=require
```

Add `psycopg2-binary==2.9.9` to `requirements.txt` and rebuild. The
SQLAlchemy models work against either backend without code changes.

## Corporate SSO

When the app sits behind a reverse proxy that handles SSO and forwards the
authenticated user in a header, swap `render_login()` in `auth.py` to read
that header instead of running the login form. The default is bcrypt + cookie
session via `streamlit-authenticator`, which is fine for getting started.

## Project layout

```
app.py                  Streamlit entry, sidebar nav, auth gate
auth.py                 bcrypt + cookie session via streamlit-authenticator
data.py                 SQLAlchemy models + CRUD
helpers.py              Date math, week buckets, holidays, capacity
theme.py                Palette + injected CSS
seed.py                 Sample workspace (idempotent)
views/                  One module per tab
exports/workbooks.py    Excel workbook builders (openpyxl)
deploy/startup.sh       Bare-metal startup script
Dockerfile              Container image
```

## Maintenance notes

- New tab: drop a module under `views/` exporting `render(audits, members, activity, role)`,
  add to `view_map` in `app.py` and the sidebar list.
- New audit field: extend `data.Audit`, update the form in `views/audit_plan.py`
  and the headers in `exports/workbooks.py`. Drop `data/workspace.db` in dev to
  let SQLAlchemy recreate the schema, or write a migration for prod.
- Branding: `theme.py` is the single source for palette and CSS. Streamlit's
  native theme colors are passed in via the Dockerfile / startup script CLI
  flags.
