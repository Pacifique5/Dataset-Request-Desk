"""add note to request status events

Revision ID: 17f4025a73fa
Revises: 9081ef80c327
Create Date: 2026-09-29 22:17:22.959726
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "17f4025a73fa"
down_revision: str | None = "9081ef80c327"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("request_status_events", sa.Column("note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("request_status_events", "note")
