from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import ACCESS_COOKIE, CurrentUser, DbSession
from app.core.config import get_settings
from app.core.rate_limit import login_limiter
from app.core.security import create_access_token, verify_password
from app.schemas.auth import LoginRequest, UserOut
from app.services.users import get_user_by_email, normalise_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, request: Request, response: Response, db: DbSession) -> UserOut:
    client_ip = request.client.host if request.client else "unknown"
    limiter_key = f"{client_ip}|{normalise_email(body.email)}"
    if retry_after := login_limiter.retry_after(limiter_key):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed sign-in attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = get_user_by_email(db, body.email)
    # Always run the hash check so unknown emails and wrong passwords look identical.
    valid = verify_password(body.password, user.password_hash if user else None)
    if not user or not valid or not user.is_active:
        login_limiter.record_failure(limiter_key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    login_limiter.reset(limiter_key)

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
