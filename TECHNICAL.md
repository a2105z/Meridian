# Meridian — Technical Details

This document explains **exactly** how Meridian is built: what talks to what, why each layer exists, and the tradeoffs behind the stack.

---

## 1. System context

Meridian is a classic three-tier web product:

1. **Browser client** (React SPA)
2. **HTTP API** (FastAPI)
3. **Relational database** (SQLite locally; Postgres via connection URL)

```text
                    ┌──────────────────────────────────────────────┐
                    │                 User Browser                 │
                    │  Meridian UI (React 18 + React Router + Vite)│
                    └──────────────────────┬───────────────────────┘
                                           │
                         HTTPS / localhost │  JSON + Bearer JWT
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │                 Meridian API                 │
                    │  FastAPI · Pydantic · Auth · Repositories    │
                    │  Middleware: CORS, request ID, timing        │
                    └──────────────────────┬───────────────────────┘
                                           │
                                SQLAlchemy │  ORM + migrations
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │              Database                        │
                    │  users · categories · entries                │
                    │  SQLite file  or  Postgres (ATLAS/FLUID/     │
                    │  MERIDIAN_DATABASE_URL)                      │
                    └──────────────────────────────────────────────┘
```

---

## 2. Frontend ↔ backend communication

### Transport

| Concern | Choice | Why |
| --- | --- | --- |
| Protocol | HTTP/JSON | Universal, easy to inspect in DevTools / OpenAPI |
| Dev proxy | Vite `/api` → `localhost:8000` | Avoids CORS pain during local development |
| Prod config | `VITE_API_URL` | Frontend can point at a deployed API origin |
| Auth header | `Authorization: Bearer <jwt>` | Stateless API auth; works for SPAs and future mobile clients |

### Auth sequence

```text
Register / Login
    │
    ▼
POST /auth/register  or  POST /auth/login
    │
    ▼
API verifies credentials (bcrypt)
    │
    ▼
API returns { access_token, user }
    │
    ▼
Frontend stores token + user in localStorage
    │
    ▼
Every /me/* request includes Bearer token
    │
    ▼
API decodes JWT → loads User → scopes queries to user.id
```

### Session restore

On app boot:

1. Read `meridian_token` from `localStorage`
2. Call `GET /auth/me`
3. If valid → enter dashboard; if 401 → clear session → login

### Core API map

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/register` | Create account → JWT |
| `POST` | `/auth/login` | Authenticate → JWT |
| `GET` | `/auth/me` | Current user profile |
| `GET` | `/me/categories` | Category list |
| `GET` | `/me/entries` | Filtered/paginated entries |
| `POST` | `/me/entries` | Create entry |
| `PATCH` | `/me/entries/{id}` | Update entry |
| `DELETE` | `/me/entries/{id}` | Delete entry |
| `GET` | `/me/reports/activity-summary` | Dashboard analytics |
| `GET` | `/me/export` | CSV or JSON export |
| `GET` | `/health` | Liveness + DB ping |

**Important security property:** there are no public `/users/{username}/...` data routes. All personal data is under `/me/*`, bound to the JWT subject. That prevents IDOR via username guessing.

---

## 3. Frontend architecture

```text
frontend/
├── index.html
└── src/
    ├── main.jsx                 # React root
    ├── App.jsx                  # Router + app state orchestration
    ├── api.js                   # fetch wrapper + token session helpers
    ├── pages/LoginPage.jsx      # Product story + auth forms
    ├── components/              # Navbar, filters, table, forms
    └── styles/styles.css        # Design system (ink + gold)
```

### Why React + Vite

| Choice | Why |
| --- | --- |
| **React 18** | Component model fits dashboard/forms; large hiring market signal |
| **Vite** | Fast HMR, simple proxy, modern ESM defaults |
| **React Router** | Real URL routes (`/login`, `/dashboard`, `/entries`) instead of fake view flags |
| **localStorage JWT** | Simple SPA session without cookie CSRF complexity for a portfolio deploy |

### UI responsibilities

- **LoginPage** — brand narrative (problem → solution animation) + auth forms
- **Dashboard** — analytics cards / category breakdown / timeline
- **Entries** — CRUD + filters + pagination
- **api.js** — single place for auth headers, 401 handling, export downloads

### Design system rationale

- **Ink background + champagne gold accent** — premium academic product feel (not generic purple SaaS)
- **Fraunces (display) + Sora (body)** — brand-first typography for a CEO-facing first impression
- **Motion** — intentional story transitions on login; subtle rise/hover elsewhere

---

## 4. Backend architecture

```text
backend/
├── app.py                 # HTTP routes + middleware + exception handlers
├── auth.py                # bcrypt + JWT helpers + get_current_user dependency
├── schemas.py             # Pydantic request/response models
├── models.py              # SQLAlchemy ORM (User, Category, Entry)
├── database.py            # engine, sessions, migrations bootstrap
├── repositories/          # DB access layer (users, entries, reports)
├── migrations/            # Alembic revision history
└── tests/                 # pytest API tests
```

### Layering

```text
Route (app.py)
  → Auth dependency (get_current_user)
  → Repository (SQLAlchemy queries)
  → Database
```

Routes stay thin. Repositories own SQL. Schemas validate I/O. Auth is injectable and reusable.

### Why FastAPI

| Choice | Why |
| --- | --- |
| **FastAPI** | Typed routes, automatic OpenAPI (`/docs`), excellent async-ready Python DX |
| **Pydantic v2** | Strict validation at the boundary (password length, username pattern, dates) |
| **SQLAlchemy** | Mature ORM; easy SQLite→Postgres switch via URL |
| **Alembic** | Schema evolution instead of “delete the DB and hope” |
| **Repository pattern** | Keeps business/API code testable and readable for reviewers |

### Auth internals

| Piece | Implementation | Why |
| --- | --- | --- |
| Password hash | `passlib` + **bcrypt** | Industry default; resists rainbow tables |
| Legacy upgrade | Detect old unsalted SHA-256 → rehash on login | Safe migration from earlier demo hashes |
| Token | **JWT** (`python-jose`) with `sub` + `uid` + `exp` | Stateless verification across processes |
| Dependency | `HTTPBearer` + `get_current_user` | Every protected route fails closed |

### Observability / robustness

- `X-Request-ID` on every response
- `X-Response-Time` timing header
- Structured 422 validation payloads
- `/health` checks DB connectivity (`SELECT 1`)
- Request logging for non-health routes

---

## 5. Data model

```text
┌──────────────┐       1        ┌──────────────┐
│    users     │───────────────<│   entries    │
│ id           │               │ id           │
│ username     │               │ user_id  (FK)│
│ names        │               │ category_id  │
│ birthday     │               │ date         │
│ password_hash│               │ details      │
│ timestamps   │               │ timestamps   │
└──────────────┘               └──────┬───────┘
                                      │
                                      │ N
                                      ▼
                               ┌──────────────┐
                               │ categories   │
                               │ id           │
                               │ name         │
                               │ slug         │
                               │ sort_order   │
                               └──────────────┘
```

- **User** owns many **Entry** rows (cascade delete)
- **Category** is normalized (not free-text-only) so analytics stay consistent
- Entries always belong to both a user and a category

---

## 6. Request lifecycle (example: create entry)

```text
1. User submits EntryForm in React
2. api.createEntry(payload)
3. fetch POST /api/me/entries
     Authorization: Bearer <token>
     Content-Type: application/json
4. Vite proxy strips /api → FastAPI /me/entries
5. get_current_user validates JWT
6. Pydantic EntryCreate validates fields
7. ReportRepository resolves category name → category_id
8. EntryRepository.create(...) inserts row
9. API returns EntryOut JSON
10. UI refreshes entries list + dashboard summary
```

---

## 7. Why these choices (decision log)

| Decision | Alternatives considered | Why Meridian’s choice wins here |
| --- | --- | --- |
| JWT in localStorage | HTTP-only cookies | Simpler SPA demo; clear auth story in code review; fine for portfolio scope |
| `/me/*` routes | `/users/{username}` | Eliminates IDOR class of bugs; teaches authz, not just authn |
| SQLite default | Postgres-only | Zero-setup local run; still Postgres-ready via env URL |
| Repository layer | SQL in route handlers | Cleaner tests and readable architecture for internship reviewers |
| React Router | Local `view` state | Real navigation, refreshable URLs, production SPA shape |
| Docker + CI | README-only | Shows ship mindset: reproducible run + automated checks |
| bcrypt over SHA-256 | Fast hashes | Correct password storage practice |

---

## 8. Local vs production topology

### Local development

```text
Browser :5173  --proxy /api-->  API :8000  -->  ./meridian.db (SQLite)
```

### Docker Compose

```text
Browser :8080 (nginx static UI)
   \-- calls API origin (VITE_API_URL) --> api :8000 --> volume DB
```

### Environment knobs

| Variable | Purpose |
| --- | --- |
| `MERIDIAN_SECRET_KEY` (or `FLUID_` / `ATLAS_` aliases) | JWT signing secret |
| `MERIDIAN_DATABASE_URL` | SQLAlchemy DB URL |
| `MERIDIAN_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `VITE_API_URL` | Frontend API base in production builds |

---

## 9. Testing strategy

`backend/tests/test_api.py` covers:

- Health endpoint
- Register / login / `/auth/me`
- Unauthenticated `/me/*` rejection (401)
- Entry isolation between users (Alice cannot read Bob’s entry)
- Authenticated export

CI (`.github/workflows/ci.yml`) runs:

1. `pytest` for backend
2. `npm ci && npm run build` for frontend

---

## 10. Security checklist (current)

- [x] Password hashing with bcrypt
- [x] JWT required for personal data
- [x] User-scoped queries (`user.id` from token, not client-supplied username)
- [x] Input validation via Pydantic
- [x] CORS restricted to localhost patterns in this portfolio setup
- [ ] For real production: rotate secrets, HTTPS only, tighter CORS allowlist, refresh tokens / cookie strategy, rate limiting

---

## 11. Mental model for reviewers

If you only remember three things:

1. **Meridian is a product**, not a CRUD toy — problem → solution UX and secure accounts.
2. **Authz is designed in** — `/me/*` + JWT subject scoping.
3. **The stack is deliberate** — FastAPI/React for speed of shipping and clarity; SQLAlchemy/Alembic for real data discipline; Docker/CI for reproducibility.
