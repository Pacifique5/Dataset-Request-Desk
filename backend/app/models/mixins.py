from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column


def str_enum(enum_cls: type[Enum], name: str) -> SAEnum:
    """VARCHAR column + CHECK constraint holding the enum *values* (not member names)."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
