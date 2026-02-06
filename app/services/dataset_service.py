"""Dataset service for managing datasets."""

from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatasetNotFoundError, ValidationError
from app.core.logging_config import get_logger
from app.models.dataset import Dataset, DatasetVersion

logger = get_logger(__name__)


class DatasetService:
    """Service for managing datasets."""

    @staticmethod
    async def get_dataset(
        session: AsyncSession, dataset_id: str
    ) -> Optional[Dataset]:
        """
        Get a dataset by ID.

        Args:
            session: Database session
            dataset_id: Dataset identifier

        Returns:
            Dataset or None if not found
        """
        result = await session.execute(
            select(Dataset).where(Dataset.id == dataset_id, Dataset.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_dataset_or_raise(
        session: AsyncSession, dataset_id: str
    ) -> Dataset:
        """
        Get a dataset by ID or raise exception if not found.

        Args:
            session: Database session
            dataset_id: Dataset identifier

        Returns:
            Dataset

        Raises:
            DatasetNotFoundError: If dataset not found
        """
        dataset = await DatasetService.get_dataset(session, dataset_id)
        if not dataset:
            raise DatasetNotFoundError(dataset_id)
        return dataset

    @staticmethod
    async def list_datasets(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        project_id: Optional[int] = None,
    ) -> list[Dataset]:
        """
        List all active datasets.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            project_id: Optional project ID to filter by

        Returns:
            List of datasets
        """
        query = select(Dataset).where(Dataset.is_active == True)

        if project_id is not None:
            query = query.where(Dataset.project_id == project_id)

        result = await session.execute(
            query.offset(skip).limit(limit).order_by(Dataset.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_dataset(
        session: AsyncSession,
        dataset_id: str,
        name: str,
        table_name: str,
        grain: str,
        schema_name: Optional[str] = None,
        description: Optional[str] = None,
        project_id: Optional[int] = None,
        source_type: str = "sql",
        uploaded_file_id: Optional[int] = None,
        created_by: str = "system",
    ) -> Dataset:
        """
        Create a new dataset.

        Args:
            session: Database session
            dataset_id: Unique dataset identifier
            name: Dataset name
            table_name: Database table name
            grain: Data grain (daily, hourly, etc.)
            schema_name: Database schema name
            description: Dataset description
            created_by: User ID who created the dataset

        Returns:
            Created dataset

        Raises:
            ValidationError: If validation fails
        """
        # Validate grain
        valid_grains = ["daily", "hourly", "weekly", "monthly"]
        if grain not in valid_grains:
            raise ValidationError(
                f"Invalid grain: {grain}. Must be one of: {valid_grains}"
            )

        # Check if dataset already exists
        existing = await DatasetService.get_dataset(session, dataset_id)
        if existing:
            raise ValidationError(f"Dataset with id '{dataset_id}' already exists")

        dataset = Dataset(
            id=dataset_id,
            name=name,
            description=description,
            table_name=table_name,
            schema_name=schema_name,
            grain=grain,
            project_id=project_id,
            source_type=source_type,
            uploaded_file_id=uploaded_file_id,
            created_by=created_by,
        )

        session.add(dataset)

        # Create initial version
        version = DatasetVersion(
            dataset_id=dataset_id,
            version=1,
            is_current=True,
            created_by=created_by,
        )
        session.add(version)

        await session.flush()
        logger.info(f"Created dataset: {dataset_id}")
        return dataset

    @staticmethod
    async def update_dataset(
        session: AsyncSession,
        dataset_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: str = "system",
    ) -> Dataset:
        """
        Update dataset metadata.

        Args:
            session: Database session
            dataset_id: Dataset identifier
            name: New name (optional)
            description: New description (optional)
            updated_by: User ID who updated

        Returns:
            Updated dataset

        Raises:
            DatasetNotFoundError: If dataset not found
        """
        dataset = await DatasetService.get_dataset_or_raise(session, dataset_id)

        if name is not None:
            dataset.name = name
        if description is not None:
            dataset.description = description

        dataset.updated_by = updated_by
        dataset.updated_at = datetime.utcnow()

        await session.flush()
        logger.info(f"Updated dataset: {dataset_id}")
        return dataset

    @staticmethod
    async def deprecate_dataset(
        session: AsyncSession, dataset_id: str, updated_by: str = "system"
    ) -> Dataset:
        """
        Deprecate (soft delete) a dataset.

        Args:
            session: Database session
            dataset_id: Dataset identifier
            updated_by: User ID who deprecated

        Returns:
            Deprecated dataset

        Raises:
            DatasetNotFoundError: If dataset not found
        """
        dataset = await DatasetService.get_dataset_or_raise(session, dataset_id)
        dataset.is_active = False
        dataset.updated_by = updated_by
        dataset.updated_at = datetime.utcnow()

        await session.flush()
        logger.info(f"Deprecated dataset: {dataset_id}")
        return dataset

