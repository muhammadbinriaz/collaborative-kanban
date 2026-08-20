# AI-Powered Collaborative Kanban

Production-oriented Kanban with a **custom FastAPI + PostgreSQL backend** (no Supabase, no Clerk). Phase 1 ships core boards, custom JWT auth, and drag-and-drop. Later phases add realtime, sprints, Groq AI, GitHub, and analytics — see [docs/roadmap.md](docs/roadmap.md).

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js (App Router), TypeScript, Tailwind, shadcn/ui, Zustand, TanStack Query, `@hello-pangea/dnd` |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Auth | Custom Argon2 passwords, access JWT, rotating refresh tokens in httpOnly cookies |
| Database | PostgreSQL 16 + pgvector. **pgAdmin 4** on port 5050 for local admin |
| Cache | Redis 7 (Celery from Phase 4) |
| Files | MinIO (dev) / S3 (prod) |
| Realtime | FastAPI WebSockets in Phase 2 — not Socket.IO |
| AI | Groq + local/pgvector embeddings in Phase 4 |

## Prerequisites

- Node.js 20+
- Python 3.11 (the Docker backend image; host 3.14 is not supported)
- Docker Desktop (recommended on Windows)

## Quick start (Docker)

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env

docker compose -f docker/docker-compose.dev.yml up --build -d

docker compose -f docker/docker-compose.dev.yml exec backend alembic upgrade head
docker compose -f docker/docker-compose.dev.yml exec backend python scripts/seed_data.py
```

Then open:

- App: http://localhost:3000
- API docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050 (login `admin@example.com` / `admin`)
- MinIO console: http://localhost:9001 (`minioadmin` / `minioadmin`)

Demo login after seed: `demo@kanban.dev` / `Demo12345!`

In pgAdmin, register host `postgres`, database `kanban`, user `kanban`, password `kanban`.

## Manual setup

Postgres, Redis, and MinIO can still run from Compose while the API and UI run on the host.

**Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

## Project structure

```
├── frontend/                 Next.js App Router
│   ├── app/
│   ├── components/kanban/    Board, lists, cards
│   ├── components/ai/        Phase 4
│   ├── components/analytics/ Phase 3
│   └── components/ui/        shadcn/ui
├── backend/
│   ├── app/api/v1/           Auth, workspaces, boards, lists, cards
│   ├── app/models/           SQLAlchemy 2.0
│   ├── app/services/
│   ├── alembic/
│   └── scripts/seed_data.py
├── docker/docker-compose.dev.yml
├── scripts/                  Repo-root helpers
└── docs/roadmap.md           Full product checklist
```

## Phase 1 API

```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me

GET|POST           /api/v1/workspaces
GET|PUT|DELETE     /api/v1/workspaces/{id}
GET|POST           /api/v1/workspaces/{id}/boards
GET|PUT|DELETE     /api/v1/boards/{id}
POST               /api/v1/boards/{id}/lists
POST               /api/v1/boards/{id}/labels
PUT|DELETE         /api/v1/lists/{id}
POST               /api/v1/lists/{id}/cards
GET|PUT|DELETE     /api/v1/cards/{id}
POST               /api/v1/cards/{id}/move
```

## Tests

```bash
cd backend
pytest
```

Frontend: `npm run lint` and `npm run type-check`.

## License

MIT
