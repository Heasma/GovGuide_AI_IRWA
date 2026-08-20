"""
GovGuide AI — Government Service Controller
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.service_schema import (
    ServiceListResponse,
    CategoryListResponse,
    ServiceSearchResponse,
    GovernmentServiceResponse,
)
from app.services.service_service import ServiceService

router = APIRouter()


@router.get(
    "/services",
    response_model=ServiceListResponse,
    summary="List government services",
)
async def list_services(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated list of official government services.
    """
    return await ServiceService.list_services(
        db, skip=skip, limit=limit, category=category, endpoint=str(request.url)
    )


@router.get(
    "/services/categories",
    response_model=CategoryListResponse,
    summary="List service categories",
)
async def list_categories(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Returns list of distinct government service categories.
    """
    return await ServiceService.list_categories(db, endpoint=str(request.url))


@router.get(
    "/services/search",
    response_model=ServiceSearchResponse,
    summary="Search government services",
)
async def search_services(
    request: Request,
    query: str = Query("", description="Search term for service name, description, category, or code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Search official government services by keywords.
    """
    return await ServiceService.search_services(
        db, query=query, skip=skip, limit=limit, endpoint=str(request.url)
    )


@router.get(
    "/services/{service_id}",
    response_model=GovernmentServiceResponse,
    summary="Get service detail",
)
async def get_service(
    service_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns complete details of a single government service.
    """
    return await ServiceService.get_service(
        db, service_id=service_id, endpoint=str(request.url)
    )
