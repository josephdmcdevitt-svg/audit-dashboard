# Ledger

Internal audit planning dashboard. Tracks engagements, allocates team hours
across a 52-week horizon, and exports formatted Excel workbooks for the
Audit Committee.

Built with Streamlit, SQLAlchemy, and openpyxl. Runs as a Databricks App,
locally, or in Docker. SQLite by default; PostgreSQL via `DATABASE_URL`.

## What it does

- **Dashboard**: KPIs, active engagement status, this-week capacity by
  person, and a 52-week utilization heatmap
- **Audit Plan**: full CRUD on engagements with phase, risk scoring
  (likelihood x impact), budgets, objectives, scope, and notes
- **Team**: roster management with per-person weekly capacity, including
  part-time hours and holiday-week adjustments
- **Executive**: traffic-light status report grouped by business unit,
  formatted for Audit Committee review
- **Activity**: append-only log of every add, edit, and delete with user
  attribution and timestamp
- **Export**: five Excel workbooks with banding, frozen panes, and
  color-coded status cells

## Data storage

All user input is persisted through SQLAlchemy into five tables defined in
`data.py`: `audits`, `team_members`, `assignments`, `notes`, and
`activity_log`. That file is the only persistence layer in the codebase.

Storage location is controlled by one environment variable:

```
DATABASE_URL=sqlite:///data/workspace.db          # default, single file
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/ledger?sslmode=require
```

The models work against either backend without code changes. Excel exports
are generated in memory and streamed to the browser; nothing is written
server-side. The app makes no external network calls and sends no telemetry.

Note for ephemeral hosts (including Databricks Apps): the container
filesystem is wiped on redeploy, so use PostgreSQL for any data that needs
to survive.

## Authentication and roles

Two modes, selected automatically:

**Databricks Apps.** No login form and no stored credentials. The app reads
the SSO identity that Databricks forwards in request headers
(`X-Forwarded-Email`). Emails listed in the `EDITOR_EMAILS` environment
variable (comma-separated, case-insensitive) get the `editor` role; everyone
else is a `viewer`.

**Local / Docker.** Username and password via streamlit-authenticator with
bcrypt hashes in `auth_config.yaml` (gitignored). On first run, set
`BOOTSTRAP_ADMIN_PASSWORD` and the app creates an `admin` editor account.
Add users by generating hashes:

```bash
python -m auth --hash YOUR_PASSWORD
```

Roles in both modes:

- `editor`: all tabs, full CRUD
- `viewer`: Dashboard and Executive, read-only

To preview the SSO path locally, set `DEV_FAKE_USER_EMAIL=you@example.com`.

## Deploy to Databricks Apps

The repo includes `app.yaml`, which is all Databricks Apps needs. The
Dockerfile is for other hosts; Databricks ignores it and installs
`requirements.txt` into its own runtime (Python 3.11, Ubuntu 22.04).

1. Sync the repo into the workspace as a Git folder.
2. Create a custom app pointing at that folder.
3. In the app's environment settings, set `EDITOR_EMAILS` to the workspace
   emails that should have edit rights. Values set here override `app.yaml`,
   so real config never needs to be committed.
4. Set `DATABASE_URL` to a PostgreSQL instance (Lakebase or any reachable
   host), referenced from a secret. Skipping this means all data is lost on
   every redeploy.
5. Deploy. Do not set ports or addresses; the runtime injects
   `STREAMLIT_SERVER_PORT` and `STREAMLIT_SERVER_ADDRESS`.

## Run locally

```bash
git clone https://github.com/josephdmcdevitt-svg/audit-dashboard.git
cd audit-dashboard
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export BOOTSTRAP_ADMIN_PASSWORD=ChooseSomethingStrong   # Windows: set ...
streamlit run app.py
```

Open http://localhost:8501 and sign in as `admin`. First start creates the
SQLite database and seeds four sample audits and a six-person team.

## Run in Docker

```bash
docker build -t ledger:latest .
docker run -d -p 8501:8501 \
  -v /srv/ledger/data:/app/data \
  -v /srv/ledger/auth_config.yaml:/app/auth_config.yaml:ro \
  --name ledger ledger:latest
```

Mount `data/` and `auth_config.yaml` from the host so the database and user
config survive restarts. For a host without Docker, `deploy/startup.sh`
installs dependencies and starts the app.

## Tests

```bash
pip install pytest
python -m pytest tests/
```

Covers the scheduling math, risk scoring, per-member capacity, and
traffic-light status logic in `helpers.py`.

## Project layout

```
app.py                  Entry point: auth gate, sidebar nav, view routing
app.yaml                Databricks Apps run command and env defaults
auth.py                 Dual-mode auth: SSO headers or local login
data.py                 SQLAlchemy models and all CRUD (only persistence layer)
helpers.py              Week math, holidays, capacity, traffic-light status
theme.py                Palette, HTML escaping, injected CSS
seed.py                 Idempotent sample workspace
views/                  One module per tab
exports/workbooks.py    Excel builders (openpyxl)
tests/                  pytest suite for helpers
.streamlit/config.toml  Server, client, and theme settings
deploy/startup.sh       Bare-metal startup script
Dockerfile              Container image for non-Databricks hosts
```

## Maintenance notes

- New tab: add a module under `views/` exporting
  `render(audits, members, activity, role)`, register it in `view_map` and
  the sidebar list in `app.py`.
- New audit field: extend `data.Audit`, update the form in
  `views/audit_plan.py` and the headers in `exports/workbooks.py`. In dev,
  delete the SQLite file to recreate the schema; in production, write a
  migration.
- Branding: `theme.py` holds the palette and injected CSS.
  `.streamlit/config.toml` holds Streamlit's native theme colors. Change
  both to restyle.
- US federal holidays are hardcoded in `helpers.py` through 2027 and need
  extending after that.
