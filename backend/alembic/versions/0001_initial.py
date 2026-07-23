"""initial

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("allocator_id", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False, server_default=""),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_allocator_id"), "users", ["allocator_id"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "investors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("remote_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_investors_id"), "investors", ["id"], unique=False)
    op.create_index(op.f("ix_investors_remote_id"), "investors", ["remote_id"], unique=True)
    op.create_index(op.f("ix_investors_name"), "investors", ["name"], unique=False)

    op.create_table(
        "funds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("remote_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_funds_id"), "funds", ["id"], unique=False)
    op.create_index(op.f("ix_funds_remote_id"), "funds", ["remote_id"], unique=True)
    op.create_index(op.f("ix_funds_name"), "funds", ["name"], unique=False)

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resource", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="running"),
        sa.Column("records_upserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("triggered_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["triggered_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sync_runs_id"), "sync_runs", ["id"], unique=False)
    op.create_index(op.f("ix_sync_runs_resource"), "sync_runs", ["resource"], unique=False)
    op.create_index(op.f("ix_sync_runs_status"), "sync_runs", ["status"], unique=False)
    op.create_index(op.f("ix_sync_runs_started_at"), "sync_runs", ["started_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sync_runs_started_at"), table_name="sync_runs")
    op.drop_index(op.f("ix_sync_runs_status"), table_name="sync_runs")
    op.drop_index(op.f("ix_sync_runs_resource"), table_name="sync_runs")
    op.drop_index(op.f("ix_sync_runs_id"), table_name="sync_runs")
    op.drop_table("sync_runs")

    op.drop_index(op.f("ix_funds_name"), table_name="funds")
    op.drop_index(op.f("ix_funds_remote_id"), table_name="funds")
    op.drop_index(op.f("ix_funds_id"), table_name="funds")
    op.drop_table("funds")

    op.drop_index(op.f("ix_investors_name"), table_name="investors")
    op.drop_index(op.f("ix_investors_remote_id"), table_name="investors")
    op.drop_index(op.f("ix_investors_id"), table_name="investors")
    op.drop_table("investors")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_allocator_id"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
