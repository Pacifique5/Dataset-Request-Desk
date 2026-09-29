"""Reusable FastAPI dependencies: DB session, authentication and role checks.

Authorization is always enforced here, on the server; the UI hiding a button is only
a convenience.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Role, User

ACCESS_COOKIE = "access_token"

DbSession = Annotated[Session, Depends(get_db)]

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def _extract_token(request: Request) -> str | None:
    """HttpOnly cookie for the browser; `Authorization: Bearer` for scripts and tests."""
    if token := request.cookies.get(ACCESS_COOKIE):
        return token
    scheme, _, credentials = request.headers.get("Authorization", "").partition(" ")
    return credentials if scheme.lower() == "bearer" and credentials else None


def get_current_user(request: Request, db: DbSession) -> User:
    token = _extract_token(request)
    user_id = decode_access_token(token) if token else None
    user = db.get(User, user_id) if user_id is not None else None
    # A deactivated user's still-valid token stops working immediately.
    if user is None or not user.is_active:
        raise _UNAUTHENTICATED
    request.state.user_id = user.id  # picked up by the request-logging middleware
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[User], User]:
    allowed = frozenset(roles)

    def checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return checker


StaffUser = Annotated[User, Depends(require_roles(Role.OPERATOR, Role.ADMIN))]
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]
ClientUser = Annotated[User, Depends(require_roles(Role.CLIENT))]
