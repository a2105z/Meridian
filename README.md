# Meridian

**Turn scattered academic achievements into one clear path.**

Meridian is a full-stack product for students who need a single, trusted system for the academic story that applications actually ask for — awards, scores, programs, experiences, goals, and reflections — with secure accounts, analytics, and export.

---

## What problem it solves

Most students keep achievements in the wrong places:

- Scores in a spreadsheet
- Awards in email threads
- Programs in Drive folders
- Goals in notes apps

When an application, interview, or advisor conversation arrives, the story is incomplete. Meridian replaces that fragmentation with one authenticated workspace.

---

## What Meridian does

| Capability | What you get |
| --- | --- |
| **Accounts** | Register / sign in with bcrypt-hashed passwords and JWT sessions |
| **Entries** | Create, edit, filter, search, sort, and paginate academic milestones |
| **Categories** | Awards, professional experiences, summer programs, test scores, AP scores, GPA, plans, goals, reflections |
| **Analytics** | Totals, first/last activity, per-category breakdowns, monthly timeline |
| **Export** | Download your data as CSV or JSON |
| **Security model** | Every data route is scoped to `/me/*` — no username-guessing IDOR |

---

## Product walkthrough

1. **Sign in / create account** — cinematic login explains the problem → solution story, then authenticates.
2. **Dashboard** — activity summary, category counts, timeline.
3. **Entries** — add and manage milestones with filters and pagination.
4. **Export** — pull a portable copy of your journey for applications or backup.

---

## Architecture (high level)

```text
┌────────────────────┐         JWT Bearer          ┌────────────────────┐
│  Meridian Web      │  ─────────────────────────► │  Meridian API      │
│  React + Vite      │     /auth/*  /me/* /health  │  FastAPI           │
│  React Router      │ ◄─────────────────────────  │  Pydantic schemas  │
└────────────────────┘         JSON / CSV          └─────────┬──────────┘
                                                             │
                                                             ▼
                                                   ┌────────────────────┐
                                                   │  SQLAlchemy ORM    │
                                                   │  Alembic migrations│
                                                   │  SQLite (default)  │
                                                   │  Postgres-ready    │
                                                   └────────────────────┘
```

For the full stack breakdown (why each choice, request flow, diagrams), see **[TECHNICAL.md](./TECHNICAL.md)**.

---

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Docker

```bash
docker compose up --build
```

---

## Tests & CI

```bash
cd backend
pytest -q
```

GitHub Actions runs backend tests + frontend production build on every push.

---

## Repo layout

```text
Meridian/
├── README.md              # Product overview (this file)
├── TECHNICAL.md           # Deep technical design
├── backend/               # FastAPI app, auth, repos, migrations, tests
├── frontend/              # React SPA (login theater, dashboard, entries)
├── docker-compose.yml
├── Dockerfile
└── .github/workflows/ci.yml
```

---

## Status

Meridian is the evolved successor of the earlier Atlas portfolio project — same academic-tracking mission, rebuilt with production-shaped auth, `/me`-scoped APIs, polished product UI, and ship tooling (Docker + CI).
