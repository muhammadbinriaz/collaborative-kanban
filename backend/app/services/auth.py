from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, Response, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=settings.COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path=settings.COOKIE_PATH,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
    )


def _issue_tokens(db: Session, user: User, response: Response) -> TokenResponse:
    raw = generate_refresh_token()
    token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw),
        expires_at=refresh_token_expiry(),
    )
    db.add(token)
    db.commit()
    _set_refresh_cookie(response, raw)
    return TokenResponse(
        access_token=create_access_token(user_id=user.id, email=user.email),
        user=UserPublic.model_validate(user),
    )


def register_user(db: Session, payload: RegisterRequest, response: Response) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        name=payload.name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(db, user, response)


def login_user(db: Session, payload: LoginRequest, response: Response) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _issue_tokens(db, user, response)


def refresh_session(db: Session, raw_token: str | None, response: Response) -> TokenResponse:
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    token_hash = hash_refresh_token(raw_token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    now = datetime.now(UTC)
    if (
        stored is None
        or stored.revoked_at is not None
        or stored.expires_at.replace(tzinfo=UTC) < now
    ):
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid")

    stored.revoked_at = now
    user = db.get(User, stored.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    db.commit()
    return _issue_tokens(db, user, response)


def logout_user(db: Session, raw_token: str | None, response: Response) -> None:
    if raw_token:
        token_hash = hash_refresh_token(raw_token)
        stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            db.commit()
    _clear_refresh_cookie(response)


def get_user_from_access_token(db: Session, token: str) -> User:
    try:
        payload = decode_access_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token"
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    user = db.get(User, UUID(user_id)) if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
