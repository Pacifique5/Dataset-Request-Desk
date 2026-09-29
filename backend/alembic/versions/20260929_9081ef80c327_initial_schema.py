"""initial schema

Revision ID: 9081ef80c327
Revises:
Create Date: 2026-09-29 21:56:19.614019
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9081ef80c327"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

KNOWN_ROBOTS = ("arm-01", "arm-02", "arm-03", "mobile-01", "humanoid-01")


def upgrade() -> None:
    robots = op.create_table(
        "robots",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_robots")),
    )
    # Reference data from seed/README.md. New robots are added by a new migration.
    op.bulk_insert(robots, [{"id": r} for r in KNOWN_ROBOTS])
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("organisation", sa.String(length=120), nullable=True),
        sa.Column(
            "role",
            sa.Enum(
                "client",
                "operator",
                "admin",
                name="user_role",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)
    op.create_table(
        "dataset_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("task_name", sa.String(length=120), nullable=False),
        sa.Column("episodes_requested", sa.Integer(), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "submitted",
                "in_progress",
                "delivered",
                "accepted",
                "rejected",
                name="request_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="submitted",
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "episodes_requested > 0", name=op.f("ck_dataset_requests_episodes_requested_positive")
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["users.id"], name=op.f("fk_dataset_requests_client_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset_requests")),
    )
    op.create_index(
        "ix_dataset_requests_client_created",
        "dataset_requests",
        ["client_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_dataset_requests_status", "dataset_requests", ["status"], unique=False)
    op.create_table(
        "episodes",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("episode_id", sa.String(length=64), nullable=False),
        sa.Column("robot_id", sa.String(length=32), nullable=False),
        sa.Column("task_name", sa.String(length=120), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("operator_name", sa.String(length=120), nullable=True),
        sa.Column(
            "quality",
            sa.Enum(
                "good",
                "usable",
                "bad",
                name="episode_quality",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("duration_seconds > 0", name=op.f("ck_episodes_duration_positive")),
        sa.ForeignKeyConstraint(
            ["robot_id"], ["robots.id"], name=op.f("fk_episodes_robot_id_robots")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_episodes")),
        sa.UniqueConstraint("episode_id", name=op.f("uq_episodes_episode_id")),
    )
    op.create_index(
        "ix_episodes_good_recorded_task",
        "episodes",
        ["recorded_at", "task_name"],
        unique=False,
        postgresql_where=sa.text("quality = 'good'"),
    )
    op.create_index(
        "ix_episodes_recorded_at_robot", "episodes", ["recorded_at", "robot_id"], unique=False
    )
    op.create_index("ix_episodes_task_quality", "episodes", ["task_name", "quality"], unique=False)
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("episode_id", sa.BigInteger(), nullable=False),
        sa.Column("assigned_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_id"], ["users.id"], name=op.f("fk_assignments_assigned_by_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["episode_id"], ["episodes.id"], name=op.f("fk_assignments_episode_id_episodes")
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["dataset_requests.id"],
            name=op.f("fk_assignments_request_id_dataset_requests"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assignments")),
        sa.UniqueConstraint("episode_id", name=op.f("uq_assignments_episode_id")),
    )
    op.create_index("ix_assignments_request", "assignments", ["request_id"], unique=False)
    op.create_table(
        "request_status_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column(
            "from_status",
            sa.Enum(
                "submitted",
                "in_progress",
                "delivered",
                "accepted",
                "rejected",
                name="event_from_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column(
            "to_status",
            sa.Enum(
                "submitted",
                "in_progress",
                "delivered",
                "accepted",
                "rejected",
                name="event_to_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("changed_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_id"],
            ["users.id"],
            name=op.f("fk_request_status_events_changed_by_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["dataset_requests.id"],
            name=op.f("fk_request_status_events_request_id_dataset_requests"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_request_status_events")),
    )
    op.create_index(
        "ix_request_status_events_request_changed",
        "request_status_events",
        ["request_id", "changed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_request_status_events_request_changed", table_name="request_status_events")
    op.drop_table("request_status_events")
    op.drop_index("ix_assignments_request", table_name="assignments")
    op.drop_table("assignments")
    op.drop_index("ix_episodes_task_quality", table_name="episodes")
    op.drop_index("ix_episodes_recorded_at_robot", table_name="episodes")
    op.drop_index(
        "ix_episodes_good_recorded_task",
        table_name="episodes",
        postgresql_where=sa.text("quality = 'good'"),
    )
    op.drop_table("episodes")
    op.drop_index("ix_dataset_requests_status", table_name="dataset_requests")
    op.drop_index("ix_dataset_requests_client_created", table_name="dataset_requests")
    op.drop_table("dataset_requests")
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_table("users")
    op.drop_table("robots")
