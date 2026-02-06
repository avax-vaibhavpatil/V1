"""Semantic layer models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SemanticDefinition(Base):
    """Semantic layer definition model."""

    __tablename__ = "semantic_definitions"

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
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="semantic_definitions")
    versions: Mapped[list["SemanticVersion"]] = relationship(
        "SemanticVersion", back_populates="semantic_definition", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SemanticDefinition(id={self.id}, name={self.name}, dataset_id={self.dataset_id})>"


class SemanticVersion(Base):
    """Semantic layer version with JSON schema."""

    __tablename__ = "semantic_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    semantic_definition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("semantic_definitions.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_json: Mapped[dict] = mapped_column(JSON, nullable=False)  # Semantic JSON schema
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    semantic_definition: Mapped["SemanticDefinition"] = relationship(
        "SemanticDefinition", back_populates="versions"
    )
    dataset_versions: Mapped[list["DatasetVersion"]] = relationship(
        "DatasetVersion", back_populates="semantic_version"
    )

    def __repr__(self) -> str:
        return (
            f"<SemanticVersion(id={self.id}, semantic_def_id={self.semantic_definition_id}, "
            f"version={self.version})>"
        )


