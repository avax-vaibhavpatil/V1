"""File upload service for CSV/XLSX files."""

import os
import csv
from typing import Optional, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.core.logging_config import get_logger
from app.models.project import UploadedFile, Project

settings = get_settings()
logger = get_logger(__name__)


class FileUploadService:
    """Service for managing file uploads."""

    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
    UPLOAD_DIR = Path("uploads")

    @staticmethod
    def _ensure_upload_dir(project_id: int) -> Path:
        """
        Ensure upload directory exists for project.

        Args:
            project_id: Project identifier

        Returns:
            Path to project upload directory
        """
        project_dir = FileUploadService.UPLOAD_DIR / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    @staticmethod
    def validate_file(filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded file.

        Args:
            filename: Original filename
            file_size: File size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if file_size > FileUploadService.MAX_FILE_SIZE:
            return (
                False,
                f"File size exceeds maximum allowed size of {FileUploadService.MAX_FILE_SIZE / (1024*1024)} MB",
            )

        # Check extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in FileUploadService.ALLOWED_EXTENSIONS:
            return (
                False,
                f"File type not allowed. Allowed types: {', '.join(FileUploadService.ALLOWED_EXTENSIONS)}",
            )

        return True, None

    @staticmethod
    async def save_uploaded_file(
        session: AsyncSession,
        project_id: int,
        filename: str,
        file_content: bytes,
        created_by: str = "system",
    ) -> UploadedFile:
        """
        Save uploaded file and create metadata record.

        Args:
            session: Database session
            project_id: Project identifier
            filename: Original filename
            file_content: File content as bytes
            created_by: User ID who uploaded

        Returns:
            Created UploadedFile record

        Raises:
            ValidationError: If validation fails
        """
        # Validate project exists
        project = await session.get(Project, project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found")

        # Validate file
        is_valid, error = FileUploadService.validate_file(filename, len(file_content))
        if not is_valid:
            raise ValidationError(error)

        # Ensure upload directory
        upload_dir = FileUploadService._ensure_upload_dir(project_id)

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(filename).suffix.lower()
        unique_filename = f"{timestamp}_{Path(filename).stem}{file_ext}"
        file_path = upload_dir / unique_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Determine file type
        file_type = "csv" if file_ext == ".csv" else "xlsx"

        # Count rows and columns (for CSV, basic implementation)
        row_count = None
        column_count = None
        if file_type == "csv":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    row_count = len(rows) - 1 if len(rows) > 1 else 0  # Exclude header
                    column_count = len(rows[0]) if rows else 0
            except Exception as e:
                logger.warning(f"Could not count CSV rows: {e}")

        # Create metadata record
        uploaded_file = UploadedFile(
            project_id=project_id,
            filename=unique_filename,
            original_filename=filename,
            file_path=str(file_path),
            file_size=len(file_content),
            file_type=file_type,
            row_count=row_count,
            column_count=column_count,
            created_by=created_by,
        )

        session.add(uploaded_file)
        await session.flush()
        logger.info(f"Saved uploaded file: {filename} for project {project_id}")
        return uploaded_file

    @staticmethod
    async def get_uploaded_file(
        session: AsyncSession, file_id: int
    ) -> Optional[UploadedFile]:
        """
        Get uploaded file by ID.

        Args:
            session: Database session
            file_id: File identifier

        Returns:
            UploadedFile or None
        """
        return await session.get(UploadedFile, file_id)

    @staticmethod
    async def list_uploaded_files(
        session: AsyncSession, project_id: int
    ) -> list[UploadedFile]:
        """
        List uploaded files for a project.

        Args:
            session: Database session
            project_id: Project identifier

        Returns:
            List of uploaded files
        """
        result = await session.execute(
            select(UploadedFile)
            .where(UploadedFile.project_id == project_id)
            .order_by(UploadedFile.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def mark_as_processed(
        session: AsyncSession, file_id: int, dataset_id: str
    ) -> UploadedFile:
        """
        Mark uploaded file as processed and link to dataset.

        Args:
            session: Database session
            file_id: File identifier
            dataset_id: Linked dataset ID

        Returns:
            Updated UploadedFile
        """
        uploaded_file = await FileUploadService.get_uploaded_file(session, file_id)
        if not uploaded_file:
            raise ValidationError(f"Uploaded file {file_id} not found")

        uploaded_file.is_processed = True
        uploaded_file.dataset_id = dataset_id

        await session.flush()
        return uploaded_file


