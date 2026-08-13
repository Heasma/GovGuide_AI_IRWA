"""
GovGuide AI — Health Controller
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.schemas import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System health check",
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Returns the health status of all system components.
    Safe to call without authentication.
    """
    # Check database connectivity (ping check)
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        version="0.1.0",
        environment=settings.APP_ENV,
        database=db_status,
        agents={
            "research_agent": "stub",
            "advisory_agent": "stub",
            "orchestrator": "stub",
            "note": "Agent stubs active — dataset integration pending",
        },
    )
