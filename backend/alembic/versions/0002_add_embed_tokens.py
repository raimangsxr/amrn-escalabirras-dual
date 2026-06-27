"""add embed_tokens table

Revision ID: 0002_add_embed_tokens
Revises: 0001_create_participants
Create Date: 2026-06-27 12:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_embed_tokens"
down_revision: str | Sequence[str] | None = "0001_create_participants"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "embed_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_embed_tokens_token_hash"),
    )
    op.create_index(
        "ix_embed_tokens_token_hash", "embed_tokens", ["token_hash"]
    )


def downgrade() -> None:
    op.drop_index("ix_embed_tokens_token_hash", table_name="embed_tokens")
    op.drop_table("embed_tokens")