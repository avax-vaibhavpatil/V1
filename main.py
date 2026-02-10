"""Analytics Studio - Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.database import init_db, close_db
from app.core.exceptions import AnalyticsStudioException
from app.api.exception_handlers import (
    analytics_studio_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.api.v1 import api_router
from fastapi.exceptions import RequestValidationError

# Setup logging
setup_logging()

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade Analytics Studio - A modular analytics platform",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(
    AnalyticsStudioException, analytics_studio_exception_handler
)
app.add_exception_handler(
    RequestValidationError, validation_exception_handler
)
app.add_exception_handler(
    Exception, generic_exception_handler
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Analytics Studio API",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
        },
    )

