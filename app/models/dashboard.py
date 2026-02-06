"""Dashboard and visualization models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Dashboard(Base):
    """Dashboard definition."""

    __tablename__ = "dashboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )  # Nullable for backward compatibility
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    layout_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Grid layout
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="dashboards")
    visuals: Mapped[list["DashboardVisual"]] = relationship(
        "DashboardVisual", back_populates="dashboard", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Dashboard(id={self.id}, name={self.name})>"


class DashboardVisual(Base):
    """Visual component in a dashboard."""

    __tablename__ = "dashboard_visuals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dashboard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dashboards.id"), nullable=False
    )
    visual_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # kpi, line, bar, table, etc.
    visual_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Visual configuration
    position: Mapped[dict] = mapped_column(JSON, nullable=False)  # Grid position
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="visuals")

    def __repr__(self) -> str:
        return (
            f"<DashboardVisual(id={self.id}, dashboard_id={self.dashboard_id}, "
            f"type={self.visual_type})>"
        )

