"""Auth module API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user, get_db
from backend.core.schemas import MessageResponse
from backend.modules.auth.models import User
from backend.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from backend.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. Optionally create a new tenant (organization).",
)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, tokens = await service.register(data)
    return {
        "user": UserResponse.model_validate(user),
        "tokens": tokens,
    }


@router.post(
    "/login",
    response_model=dict,
    summary="Log in with email and password",
    description="Authenticate and receive JWT access and refresh tokens.",
)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, tokens = await service.login(data)
    return {
        "user": UserResponse.model_validate(user),
        "tokens": tokens,
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access/refresh token pair.",
)
async def refresh_token(
    data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    return await service.refresh_token(data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.update_profile(
        current_user,
        full_name=data.full_name,
        avatar_url=data.avatar_url,
    )
    return UserResponse.model_validate(user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.change_password(
        current_user, data.current_password, data.new_password
    )
    return MessageResponse(message="Password changed successfully")
