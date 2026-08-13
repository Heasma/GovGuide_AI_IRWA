"""
GovGuide AI — FastAPI Application Entry Point
"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.controllers import (
    auth_router,
    query_router,
    service_router,
    session_router,
    admin_router,
    health_router,
)

# ── Logging setup ─────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger(__name__)
settings = get_settings()


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("govguide_api_starting", env=settings.APP_ENV)
    yield
    logger.info("govguide_api_stopped")


# ── App factory ──────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    application = FastAPI(
        title="GovGuide AI",
        description=(
            "An Agentic AI-Based Government Service Discovery, "
            "Eligibility and Information Retrieval Platform.\n\n"
            "**Note:** Government dataset integration is pending. "
            "Service endpoints currently return placeholder responses."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Controllers ──────────────────────────────────────────────────────────
    prefix = "/api/v1"
    application.include_router(health_router, prefix=prefix, tags=["Health"])
    application.include_router(auth_router, prefix=prefix, tags=["Authentication"])
    application.include_router(query_router, prefix=prefix, tags=["AI Query"])
    application.include_router(service_router, prefix=prefix, tags=["Services"])
    application.include_router(session_router, prefix=prefix, tags=["Sessions"])
    application.include_router(admin_router, prefix=prefix, tags=["Admin"])

    # ── Global exception handler ──────────────────────────────────────────────
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )

    return application


app = create_app()
