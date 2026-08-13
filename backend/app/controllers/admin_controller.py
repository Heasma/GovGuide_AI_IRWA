"""
GovGuide AI — Admin Controller
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import require_admin
from app.schemas import AdminUserRecord, AdminAuditLogRecord, AdminAgentLogRecord
from app.services.auth_service import AuthService
from app.services.session_service import SessionService

router = APIRouter()


@router.get(
    "/admin/users",
    response_model=List[AdminUserRecord],
    summary="List all users",
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns list of registered users. Admin role required.
    """
    return await AuthService.list_users(db, skip=skip, limit=limit)


@router.get(
    "/admin/audit-logs",
    response_model=List[AdminAuditLogRecord],
    summary="Query audit logs",
)
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    event_type: str = Query(None),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns security audit log records. Admin role required.
    """
    return await SessionService.get_audit_logs(db, skip=skip, limit=limit, event_type=event_type)


@router.get(
    "/admin/agent-logs",
    response_model=List[AdminAgentLogRecord],
    summary="Query agent interaction logs",
)
async def get_agent_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns orchestrator-agent interaction log records. Admin role required.
    """
    return await SessionService.get_agent_logs(db, skip=skip, limit=limit)
