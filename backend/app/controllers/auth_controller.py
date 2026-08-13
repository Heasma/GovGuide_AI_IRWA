"""
GovGuide AI — Authentication Controller
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfile,
)
from app.services.auth_service import AuthService
from app.services.exceptions import (
    DuplicateUserError,
    InvalidCredentialsError,
    InactiveUserError,
    InvalidTokenError,
    UserNotFoundError,
)

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post(
    "/auth/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account with role 'public'."""
    try:
        result = await AuthService.register(db, body.email, body.password)
        return result
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Login",
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and return JWT access + refresh tokens."""
    ip = request.client.host if request.client else "unknown"
    try:
        result = await AuthService.login(db, body.email, body.password, ip)
        return result
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Use a refresh token to obtain a new access token."""
    try:
        result = await AuthService.refresh_token(db, body.refresh_token)
        return result
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.post(
    "/auth/logout",
    summary="Logout",
)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Invalidates the current session.
    """
    logger.info("user_logout", user_id=current_user["user_id"])
    return {"message": "Logged out successfully."}


@router.get(
    "/auth/me",
    response_model=UserProfile,
    summary="Get current user profile",
)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the authenticated user's profile."""
    try:
        profile = await AuthService.get_profile(db, current_user["user_id"])
        return profile
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
