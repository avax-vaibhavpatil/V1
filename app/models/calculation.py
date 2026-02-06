"""Calculation and measure models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CalculatedMeasure(Base):
    """Calculated measure definition."""

    __tablename__ = "calculated_measures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("datasets.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    versions: Mapped[list["MeasureVersion"]] = relationship(
        "MeasureVersion", back_populates="measure", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CalculatedMeasure(id={self.id}, name={self.name}, dataset_id={self.dataset_id})>"


class MeasureVersion(Base):
    """Version of a calculated measure formula."""

    __tablename__ = "measure_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    measure_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("calculated_measures.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    formula: Mapped[str] = mapped_column(Text, nullable=False)  # DSL formula
    validation_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    measure: Mapped["CalculatedMeasure"] = relationship(
        "CalculatedMeasure", back_populates="versions"
    )

    def __repr__(self) -> str:
        return (
            f"<MeasureVersion(id={self.id}, measure_id={self.measure_id}, "
            f"version={self.version}, is_valid={self.is_valid})>"
        )


