"""add event singleton table

Revision ID: 0003_add_event
Revises: 0002_add_embed_tokens
Create Date: 2026-06-28 10:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_event"
down_revision: str | Sequence[str] | None = "0002_add_embed_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SEED_TITLE = "II Torneo Motero de Escalabirras"
SEED_SUBTITLE = "XV Concentración Motera Ría de Noia"


def upgrade() -> None:
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("subtitle", sa.String(length=80), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    event_table = sa.table(
        "event",
        sa.column("id", sa.Integer),
        sa.column("title", sa.String),
        sa.column("subtitle", sa.String),
    )
    op.bulk_insert(event_table, [{"id": 1, "title": SEED_TITLE, "subtitle": SEED_SUBTITLE}])


def downgrade() -> None:
    op.drop_table("event")
