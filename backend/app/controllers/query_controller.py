"""
GovGuide AI — Query Controller
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import QueryRequest, FeedbackRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Submit natural language query to the AI assistant",
)
async def submit_query(
    body: QueryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Routes the user's query through the QueryService.
    """
    user_id = current_user.get("user_id")
    ip = request.client.host if request.client else "unknown"

    try:
        result = await QueryService.process_query(
            db=db,
            query=body.query,
            session_id=body.session_id,
            user_id=user_id,
            ip_address=ip,
        )
        return result
    except Exception as exc:
        logger.error("query_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The AI assistant encountered an error processing your request.",
        )


@router.post(
    "/query/{request_id}/feedback",
    status_code=status.HTTP_200_OK,
    summary="Submit feedback on an AI response",
)
async def submit_feedback(
    request_id: str,
    body: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Records user feedback (helpful / not helpful).
    """
    logger.info(
        "feedback_received",
        request_id=request_id,
        user_id=current_user["user_id"],
        rating=body.rating,
    )
    return {"message": "Feedback recorded. Thank you."}
