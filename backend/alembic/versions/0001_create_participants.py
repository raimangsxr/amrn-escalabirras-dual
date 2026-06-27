"""create participants table

Revision ID: 0001_create_participants
Revises:
Create Date: 2026-06-27 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_participants"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column(
            "crates",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("crates >= 0", name="ck_participants_crates_nonneg"),
    )
    op.create_index(
        "ix_participants_created_at_desc",
        "participants",
        [sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_participants_crates_desc",
        "participants",
        [sa.text("crates DESC"), sa.text("created_at ASC")],
    )


def downgrade() -> None:
    op.drop_index("ix_participants_crates_desc", table_name="participants")
    op.drop_index("ix_participants_created_at_desc", table_name="participants")
    op.drop_table("participants")