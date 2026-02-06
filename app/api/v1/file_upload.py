"""File upload API routes."""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form

from app.core.dependencies import DatabaseDep, RequireRead, RequireWrite
from app.core.exceptions import ValidationError
from app.services.file_upload_service import FileUploadService

router = APIRouter()


@router.get("/project/{project_id}")
async def list_uploaded_files(
    project_id: int,
    db: DatabaseDep,
    user: RequireRead,
):
    """List uploaded files for a project."""
    files = await FileUploadService.list_uploaded_files(db, project_id)
    return files


@router.get("/{file_id}")
async def get_uploaded_file(
    file_id: int,
    db: DatabaseDep,
    user: RequireRead,
):
    """Get uploaded file metadata by ID."""
    uploaded_file = await FileUploadService.get_uploaded_file(db, file_id)
    if not uploaded_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    return uploaded_file


@router.post("/upload")
async def upload_file(
    db: DatabaseDep,
    user: RequireWrite,
    project_id: int = Form(...),
    file: UploadFile = File(...),
):
    """Upload a CSV or XLSX file."""
    try:
        # Read file content
        file_content = await file.read()

        # Save file
        uploaded_file = await FileUploadService.save_uploaded_file(
            session=db,
            project_id=project_id,
            filename=file.filename or "unknown",
            file_content=file_content,
            created_by=user.get("id", "system"),
        )

        await db.commit()
        return uploaded_file

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/{file_id}/mark-processed")
async def mark_file_processed(
    file_id: int,
    db: DatabaseDep,
    user: RequireWrite,
    dataset_id: str = Form(...),
):
    """Mark uploaded file as processed and link to dataset."""
    try:
        uploaded_file = await FileUploadService.mark_as_processed(
            db, file_id, dataset_id
        )
        await db.commit()
        return uploaded_file
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


