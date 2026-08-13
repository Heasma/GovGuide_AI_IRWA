"""
GovGuide AI — Government Service Controller
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import DatasetPendingResponse
from app.services.service_service import ServiceService

router = APIRouter()


@router.get(
    "/services",
    response_model=DatasetPendingResponse,
    summary="List government services",
)
async def list_services(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Returns pending status for services list.
    """
    return await ServiceService.list_services(db, endpoint=str(request.url))


@router.get(
    "/services/categories",
    response_model=DatasetPendingResponse,
    summary="List service categories",
)
async def list_categories(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Returns pending status for categories list.
    """
    return await ServiceService.list_categories(db, endpoint=str(request.url))


@router.get(
    "/services/search",
    response_model=DatasetPendingResponse,
    summary="Search government services",
)
async def search_services(request: Request, query: str = "", db: AsyncSession = Depends(get_db)):
    """
    Returns pending status for service search.
    """
    return await ServiceService.search_services(db, query=query, endpoint=str(request.url))


@router.get(
    "/services/{service_id}",
    response_model=DatasetPendingResponse,
    summary="Get service detail",
)
async def get_service(service_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Returns pending status for a single service.
    """
    return await ServiceService.get_service(db, service_id=service_id, endpoint=str(request.url))
