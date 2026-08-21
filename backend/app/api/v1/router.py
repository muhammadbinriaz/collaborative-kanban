from fastapi import APIRouter

from app.api.v1 import (
    ai,
    attachments,
    auth,
    boards,
    cards,
    collaboration,
    github,
    lists,
    sprints,
    whiteboards,
    workspaces,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(boards.router)
api_router.include_router(lists.router)
api_router.include_router(cards.router)
api_router.include_router(collaboration.router)
api_router.include_router(sprints.router)
api_router.include_router(ai.router)
api_router.include_router(attachments.router)
api_router.include_router(github.router)
api_router.include_router(whiteboards.router)
