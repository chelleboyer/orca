"""
Authentication endpoints for user registration, login, and profile management
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_from_token
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    LoginResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    MessageResponse,
    ErrorResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance"""
    return AuthService(db)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new user account with email, password, and display name",
    responses={
        201: {"description": "User successfully registered"},
        400: {"model": ErrorResponse, "description": "Invalid input or user already exists"},
        422: {"description": "Validation error"},
    }
)
async def register_user(
    user_data: UserRegister,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Register a new user account.
    
    **Requirements:**
    - Valid email format (RFC 5322 compliant)
    - Password: minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 number
    - Display name: 2-50 characters, alphanumeric and spaces only
    
    **Returns:**
    - User profile information (excludes sensitive data)
    - Success message about email verification
    """
    return await auth_service.register_user(user_data)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate user with email and password",
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials or account disabled"},
        429: {"model": ErrorResponse, "description": "Too many login attempts"},
        422: {"description": "Validation error"},
    }
)
async def login_user(
    login_data: UserLogin,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Authenticate user and return access token.
    
    **Security Features:**
    - Rate limiting: max 5 attempts per minute per IP
    - Secure password verification using Argon2
    - JWT access token with 30-minute expiration
    - Session management in Redis
    
    **Returns:**
    - JWT access token
    - Token expiration time
    - User profile information
    """
    client_ip = request.client.host if request.client else "unknown"
    
    user, access_token, expires_in = await auth_service.authenticate_user(login_data, client_ip)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=user
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Logout user and invalidate current session",
    dependencies=[Depends(get_current_user_from_token)],
    responses={
        200: {"description": "Logout successful"},
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
    }
)
async def logout_user(
    current_user: Annotated[dict, Depends(get_current_user_from_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Logout user by invalidating current session.
    
    **Security Features:**
    - Invalidates session in Redis
    - Adds token to blacklist
    - Prevents token reuse
    
    **Requires:**
    - Valid JWT token in Authorization header
    """
    user_id = uuid.UUID(current_user["user_id"])
    token = current_user["token"]
    
    await auth_service.logout_user(user_id, token)
    
    return MessageResponse(message="Successfully logged out")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Initiate password reset",
    description="Send password reset instructions to user's email",
    responses={
        200: {"description": "Password reset instructions sent (if account exists)"},
        429: {"model": ErrorResponse, "description": "Too many password reset attempts"},
        422: {"description": "Validation error"},
    }
)
async def forgot_password(
    reset_data: ForgotPasswordRequest,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Initiate password reset process.
    
    **Security Features:**
    - Rate limiting: max 3 attempts per 5 minutes per IP
    - No user enumeration (same response regardless of email existence)
    - Secure reset token generation
    - Token expires in 15 minutes
    
    **Always returns success message for security reasons.**
    """
    client_ip = request.client.host if request.client else "unknown"
    
    message = await auth_service.initiate_password_reset(reset_data, client_ip)
    
    return MessageResponse(message=message)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
    description="Reset user password using reset token",
    responses={
        200: {"description": "Password successfully reset"},
        400: {"model": ErrorResponse, "description": "Invalid or expired reset token"},
        422: {"description": "Validation error"},
    }
)
async def reset_password(
    reset_data: ResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Reset user password using reset token.
    
    **Requirements:**
    - Valid reset token (received via email)
    - New password: minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 number
    
    **Security Features:**
    - Single-use reset tokens
    - Token expiration (15 minutes)
    - Invalidates all existing user sessions
    - Same password validation as registration
    """
    message = await auth_service.reset_password(reset_data)
    
    return MessageResponse(message=message)


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get user profile",
    description="Get current user's profile information",
    dependencies=[Depends(get_current_user_from_token)],
    responses={
        200: {"description": "User profile retrieved"},
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        404: {"model": ErrorResponse, "description": "User not found"},
    }
)
async def get_user_profile(
    current_user: Annotated[dict, Depends(get_current_user_from_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Get current user's profile information.
    
    **Returns:**
    - User ID, email, display name
    - Account creation and last login timestamps
    - Account status and email verification status
    
    **Requires:**
    - Valid JWT token in Authorization header
    """
    user_id = uuid.UUID(current_user["user_id"])
    
    return auth_service.get_user_profile(user_id)


@router.patch(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update current user's profile information",
    dependencies=[Depends(get_current_user_from_token)],
    responses={
        200: {"description": "Profile successfully updated"},
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        404: {"model": ErrorResponse, "description": "User not found"},
        422: {"description": "Validation error"},
    }
)
async def update_user_profile(
    update_data: UpdateProfileRequest,
    current_user: Annotated[dict, Depends(get_current_user_from_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Update current user's profile information.
    
    **Updatable fields:**
    - Display name (2-50 characters, alphanumeric and spaces only)
    
    **Future enhancements:**
    - Email updates with re-verification
    - Profile picture uploads
    - Additional profile fields
    
    **Requires:**
    - Valid JWT token in Authorization header
    """
    user_id = uuid.UUID(current_user["user_id"])
    
    return auth_service.update_user_profile(user_id, update_data)


@router.post(
    "/verify-email/{verification_token}",
    response_model=MessageResponse,
    summary="Verify email address",
    description="Verify user's email address using verification token",
    responses={
        200: {"description": "Email successfully verified"},
        400: {"model": ErrorResponse, "description": "Invalid verification token"},
    }
)
async def verify_email(
    verification_token: str,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Verify user's email address using verification token.
    
    **Process:**
    - Validates verification token
    - Marks email as verified
    - Clears verification token
    
    **Typically called from email verification link.**
    """
    message = auth_service.verify_email(verification_token)
    
    return MessageResponse(message=message)
