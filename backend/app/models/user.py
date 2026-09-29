from sqlalchemy import Boolean, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import Role
from app.models.mixins import CreatedAtMixin, str_enum


class User(CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # Case-insensitive uniqueness: "Ada@x.com" and "ada@x.com" are the same account.
        Index("uq_users_email_lower", text("lower(email)"), unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    organisation: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(str_enum(Role, "user_role"), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
