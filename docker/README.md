# Copy env files, then from the repo root:
#   docker compose -f docker/docker-compose.dev.yml up --build
#   docker compose -f docker/docker-compose.dev.yml exec backend alembic upgrade head
#   docker compose -f docker/docker-compose.dev.yml exec backend python scripts/seed_data.py
