from fastapi import APIRouter

from app.api.v1 import auth, boards, cards, lists, workspaces

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(boards.router)
api_router.include_router(lists.router)
api_router.include_router(cards.router)
