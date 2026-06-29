"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Participant(Base):
    """A participant in the escalabirras tournament.

    See ``specs/contracts/persistence-postgres/contract.md`` for the
    authoritative schema description.
    """

    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    crates: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"Participant(id={self.id!r}, name={self.name!r}, crates={self.crates!r})"


class EmbedToken(Base):
    """A long-lived credential issued by the operator to bypass login.

    The plaintext token is shown exactly once at creation. Only the
    sha256 hex digest is stored here. See
    ``specs/contracts/persistence-postgres/contract.md``.
    """

    __tablename__ = "embed_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"EmbedToken(id={self.id!r}, name={self.name!r}, revoked={self.revoked_at is not None})"


class Event(Base):
    """Tournament display info edited by the operator from ``/admin``.

    Logically a singleton: there is exactly one row (``id = 1``) in
    normal operation. The synthetic PK leaves room for a future
    multi-event schema. See
    ``specs/contracts/persistence-postgres/contract.md``.
    """

    __tablename__ = "event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(80), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"Event(id={self.id!r}, title={self.title!r})"