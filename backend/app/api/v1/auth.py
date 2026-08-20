from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, DbSession, RefreshCookie
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, response: Response, db: DbSession) -> TokenResponse:
    return auth_service.register_user(db, payload, response)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: DbSession) -> TokenResponse:
    return auth_service.login_user(db, payload, response)


@router.post("/refresh", response_model=TokenResponse)
def refresh(response: Response, db: DbSession, refresh_token: RefreshCookie) -> TokenResponse:
    return auth_service.refresh_session(db, refresh_token, response)


@router.post("/logout", status_code=204)
def logout(response: Response, db: DbSession, refresh_token: RefreshCookie) -> None:
    auth_service.logout_user(db, refresh_token, response)


@router.get("/me", response_model=UserPublic)
def me(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)
