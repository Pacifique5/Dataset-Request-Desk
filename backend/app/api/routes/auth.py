from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import ACCESS_COOKIE, CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.schemas.auth import LoginRequest, UserOut
from app.services.users import get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: DbSession) -> UserOut:
    user = get_user_by_email(db, body.email)
    # Always run the hash check so unknown emails and wrong passwords look identical.
    valid = verify_password(body.password, user.password_hash if user else None)
    if not user or not valid or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    settings = get_settings()
    response.set_cookie(
        ACCESS_COOKIE,
        create_access_token(user.id),
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,  # not readable from JavaScript (XSS can't steal it)
        samesite="lax",  # not sent on cross-site POSTs (CSRF mitigation)
        secure=settings.cookie_secure,
        path="/",
    )
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
