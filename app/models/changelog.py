"""Changelog model for tracking changes."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base


class ChangeType(str, enum.Enum):
    """Types of changes tracked."""

    CALCULATION = "calculation"
    SEMANTIC = "semantic"
    DASHBOARD = "dashboard"
    DATASET = "dataset"
    USER = "user"
    PERMISSION = "permission"


class Changelog(Base):
    """Changelog entry for tracking all changes."""

    __tablename__ = "changelog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    change_type: Mapped[ChangeType] = mapped_column(Enum(ChangeType), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # created, updated, deleted
    changes: Mapped[dict] = mapped_column(JSON, nullable=False)  # What changed
    impacted_assets: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Affected dashboards, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Changelog(id={self.id}, type={self.change_type}, "
            f"entity={self.entity_type}:{self.entity_id}, action={self.action})>"
        )


