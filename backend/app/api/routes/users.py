from fastapi import APIRouter, status

from app.api.deps import AdminUser, DbSession
from app.schemas.auth import UserCreate, UserOut, UserUpdate
from app.services import users as svc

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_(db: DbSession, _: AdminUser) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in svc.list_users(db)]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create(body: UserCreate, db: DbSession, _: AdminUser) -> UserOut:
    user = svc.register_user(db, body)
    db.commit()
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
def update(user_id: int, body: UserUpdate, db: DbSession, admin: AdminUser) -> UserOut:
    user = svc.update_user(db, admin, user_id, body)
    db.commit()
    return UserOut.model_validate(user)
