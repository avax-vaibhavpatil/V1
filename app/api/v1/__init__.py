"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import (
    datasets,
    semantic,
    calculations,
    dashboards,
    query,
    changelog,
    projects,
    database_connections,
    file_upload,
    dependency_safety,
    reports,
)

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(semantic.router, prefix="/semantic", tags=["semantic"])
api_router.include_router(calculations.router, prefix="/calculations", tags=["calculations"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(changelog.router, prefix="/changelog", tags=["changelog"])
api_router.include_router(
    database_connections.router, prefix="/database-connections", tags=["database-connections"]
)
api_router.include_router(file_upload.router, prefix="/files", tags=["file-upload"])
api_router.include_router(
    dependency_safety.router, prefix="/dependency-safety", tags=["dependency-safety"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

