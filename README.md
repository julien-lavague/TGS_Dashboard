# TGS Metrics Dashboard

Internal metrics dashboard for The Good Spots — FastAPI backend + Next.js frontend.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A Supabase project with `users` and `user_alerts` tables
- An Anthropic API key (for the topic-analysis feature)

---

## Configuration

Copy `.env.example` to `.env` at the project root and fill in the values:

```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_API_KEY=<service-role or anon key>
ANTHROPIC_API_KEY=<sk-ant-...>
DASHBOARD_USER=admin
DASHBOARD_PASSWORD=<choose a password>
CORS_ORIGINS=http://localhost:3000
```

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | yes | Your Supabase project URL |
| `SUPABASE_API_KEY` | yes | Supabase service-role key |
| `ANTHROPIC_API_KEY` | yes | Used by the Topic Analysis job |
| `DASHBOARD_USER` / `DASHBOARD_PASSWORD` | yes | Basic-auth credentials for the dashboard |
| `CORS_ORIGINS` | yes | Comma-separated allowed origins; keep `http://localhost:3000` for local dev |

---

## Starting the backend

```powershell
# From the project root
cd backend
python -m venv ..\.venv          # only on first run
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # only on first run or after changes

uvicorn main:app --reload --port 8000
```

The API is then available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`  
Health check: `http://localhost:8000/health`

> The backend reads `.env` from the **parent directory** of `backend/` (i.e. the project root).

---

## Starting the frontend

```powershell
cd frontend
npm install   # only on first run
npm run dev
```

Open `http://localhost:3000` — it redirects to `/overview`.

---

## App structure

### Backend (`backend/`)

| Path | Role |
|---|---|
| `main.py` | FastAPI app — CORS config, router registration |
| `config.py` | Settings loaded from `.env` via pydantic-settings |
| `db/supabase_client.py` | Supabase singleton + `get_dataframe()` helper |
| `core/user_segments.py` | Email lists & `filter_users()` for release / beta / all segments |
| `routers/alerts.py` | `GET /api/alerts/schedule` |
| `routers/overview.py` | User-growth, messages-over-time, topic-analysis endpoints |
| `routers/usage.py` | Usage metrics endpoints |
| `services/alerts_service.py` | Joins `user_alerts` + `users`, explodes schedule rows |
| `schemas/alerts.py` | Pydantic response models |

### Frontend (`frontend/`)

| Route | Page |
|---|---|
| `/overview` | New users per week, messages over time, AI topic analysis |
| `/alerts` | Alert schedule table |
| `/usage` | Usage metrics |
| `/profils` | User profiles |
| `/equipments` | Equipment data |

---

## User segments

Three segments are available on every page that supports filtering:

| Segment | Meaning |
|---|---|
| `release` | Real users only — excludes internal, beta, friends, work contacts |
| `beta` | Early beta testers invited before public launch |
| `all` | Everyone, no filter |

The lists are maintained in `backend/core/user_segments.py`.
