from collections.abc import Generator
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.auth import get_user_from_access_token

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return get_user_from_access_token(db, credentials.credentials)


def get_refresh_cookie(refresh_token: Optional[str] = Cookie(default=None)) -> Optional[str]:
    return refresh_token


CurrentUser = Annotated[User, Depends(get_current_user)]
RefreshCookie = Annotated[Optional[str], Depends(get_refresh_cookie)]


def parse_uuid(value: str, label: str = "id") -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid {label}") from exc


def get_db_dep() -> Generator[Session, None, None]:
    yield from get_db()
