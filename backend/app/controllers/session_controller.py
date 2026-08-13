"""
GovGuide AI — Session Controller
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import SessionSummary
from app.services.session_service import SessionService
from app.services.exceptions import SessionNotFoundError

router = APIRouter()


@router.get(
    "/sessions",
    response_model=List[SessionSummary],
    summary="List user sessions",
)
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns a list of the authenticated user's query sessions."""
    return await SessionService.list_sessions(db, current_user["user_id"])


@router.get(
    "/sessions/{session_id}/messages",
    summary="Get session messages",
)
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all messages in a session owned by the current user."""
    try:
        messages = await SessionService.get_session_messages(db, session_id, current_user["user_id"])
        return messages
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.delete(
    "/sessions/{session_id}",
    summary="Delete a session",
)
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a session owned by the current user."""
    try:
        await SessionService.delete_session(db, session_id, current_user["user_id"])
        return {"message": "Session deleted."}
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
