# Product roadmap

The full product vision stays here. Implementation is phased. Do not treat unchecked items as missing from a broken v1 — they are scheduled.

## Phase 1 — Core Kanban

- [x] Docker Compose: Postgres 16 + pgvector, Redis, MinIO, pgAdmin, backend, frontend
- [x] FastAPI skeleton, settings, CORS, structured logging
- [x] SQLAlchemy models + Alembic: users, workspaces, members, boards, lists, cards, labels
- [x] Custom auth: register, login, refresh, logout, `GET /me`
- [x] Workspace + board + list + card CRUD
- [x] Drag-and-drop move (`POST /cards/{id}/move` with position)
- [x] Next.js app: login/register, workspace list, board view
- [x] Seed script for a demo workspace

## Phase 2 — Collaboration (current)

- [x] Roles enforced across every mutation (owner / admin / member / viewer)
- [x] Invites (share link first; email later)
- [x] Comments + @mentions
- [x] Activity / audit log
- [x] FastAPI WebSockets: board sync (`/ws/boards/{id}`) + presence (`/ws/presence`)
- [x] In-app notifications

## Phase 3 — Sprints and analytics

- [ ] Sprint lifecycle (plan, start, complete)
- [ ] Card estimates + assignment UX
- [ ] Burndown, velocity, workload charts (Recharts)
- [ ] Stale-task / bottleneck queries (rules first, AI later)

## Phase 4 — AI project manager

- [ ] Groq client + prompt templates (`GROQ_MODEL=llama-3.3-70b-versatile`)
- [ ] Prioritization, standup summary, risk detection, workload balance, sprint plan
- [ ] Embeddings + similar/duplicate task search (pgvector)
- [ ] Predictive dates from historical cycle time
- [ ] Celery jobs for slow AI work
- [ ] AI UI panels on the board (`frontend/components/ai`)

## Phase 5 — Integrations and production

- [ ] Card attachments (MinIO in dev / S3 in prod)
- [ ] GitHub OAuth, repo connect, PR/commit webhooks
- [ ] Email (verification, invites, notifications)
- [ ] Sentry, GitHub Actions CI, prod compose / Nginx
- [ ] Load tests for WebSockets

## Later (v2)

- [ ] Slack integration
- [ ] Mobile apps
- [ ] Public third-party API
- [ ] Custom AI models
- [ ] Enterprise SSO
