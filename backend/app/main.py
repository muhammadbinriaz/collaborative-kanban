from app import models  # noqa: F401 — register SQLAlchemy mappers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.websocket.routes import router as ws_router

setup_logging()

app = FastAPI(
    title="AI Kanban API",
    version="0.2.0",
    description="Custom FastAPI backend for the AI-powered collaborative Kanban app.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}
