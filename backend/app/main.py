from app import models  # noqa: F401 — register SQLAlchemy mappers

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.collab.excalidraw_room import sio
from app.core.config import settings
from app.core.logging import setup_logging
from app.websocket.routes import router as ws_router

setup_logging()

if settings.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 0.0,
    )

app = FastAPI(
    title="AI Kanban API",
    version="0.6.0",
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


# Excalidraw-room compatible Socket.IO ASGI wrapper (websocket + HTTP polling).
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
