from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return current UTC datetime with explicit timezone. Use as default/onupdate for timestamp columns."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarative class for future SQLAlchemy models."""


class TimestampMixin:
    """Reusable timestamp fields for database models.

    Uses Python-level utc_now() instead of SQL function func.now()
    to ensure consistent UTC timezone handling across all database engines.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
