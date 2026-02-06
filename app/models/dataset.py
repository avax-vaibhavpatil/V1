"""Dataset models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Dataset(Base):
    """Dataset metadata model."""

    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )  # Nullable for backward compatibility
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    table_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    schema_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    grain: Mapped[str] = mapped_column(String(50), nullable=False)  # daily, hourly, etc.
    source_type: Mapped[str] = mapped_column(
        String(50), default="sql", nullable=False
    )  # sql, uploaded_file
    uploaded_file_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("uploaded_files.id"), nullable=True
    )  # If source is uploaded file
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="datasets")
    versions: Mapped[list["DatasetVersion"]] = relationship(
        "DatasetVersion", back_populates="dataset", cascade="all, delete-orphan"
    )
    semantic_definitions: Mapped[list["SemanticDefinition"]] = relationship(
        "SemanticDefinition", back_populates="dataset"
    )

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name}, table={self.table_name})>"


class DatasetVersion(Base):
    """Dataset version tracking."""

    __tablename__ = "dataset_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("datasets.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    semantic_version_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("semantic_versions.id"), nullable=True
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="versions")
    semantic_version: Mapped[Optional["SemanticVersion"]] = relationship(
        "SemanticVersion", back_populates="dataset_versions"
    )

    def __repr__(self) -> str:
        return f"<DatasetVersion(dataset_id={self.dataset_id}, version={self.version})>"

