from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
from app.core.config import Settings, get_settings
from datetime import datetime, UTC

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    app_name: str
    version: str
    openrouter_configured: bool


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Health check endpoint.
    Returns application status and configuration info.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        openrouter_configured=bool(settings.OPENROUTER_API_KEY)
    )


@router.get("/health/detailed", tags=["Health"])
async def detailed_health_check(settings: Settings = Depends(get_settings)):
    """
    Detailed health check with configuration details.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG
        },
        "openrouter": {
            "configured": bool(settings.OPENROUTER_API_KEY),
            "base_url": settings.OPENROUTER_BASE_URL,
            "model": settings.OPENROUTER_MODEL,
            "timeout": settings.OPENROUTER_TIMEOUT
        },
        "database": {
            "url": settings.DATABASE_URL.split("///")[0] + "///" + "***"  # Hide sensitive info
        }
    }
