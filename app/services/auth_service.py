"""
Authentication service with business logic for user management
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.auth import (
    UserRegister, 
    UserLogin, 
    UserResponse, 
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest
)
from app.core.security import (
    security_utils, 
    session_manager, 
    rate_limiter,
    token_blacklist
)
from app.core.config import settings


class AuthService:
    """Authentication service for user registration, login, and profile management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def register_user(self, user_data: UserRegister) -> UserResponse:
        """Register a new user"""
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password
        password_hash = security_utils.hash_password(user_data.password)
        
        # Generate verification token
        verification_token = security_utils.generate_verification_token()
        
        # Create user
        db_user = User(
            email=user_data.email,
            name=user_data.name,
            password_hash=password_hash,
            verification_token=verification_token,
            email_verified=False,  # Email verification required
            is_active=True
        )
        
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # TODO: Send verification email (will be implemented in email service)
        # await self.send_verification_email(db_user.email, verification_token)
        
        return UserResponse.from_orm(db_user)
    
    async def authenticate_user(
        self, 
        login_data: UserLogin, 
        client_ip: str
    ) -> Tuple[UserResponse, str, int]:
        """Authenticate user and return user data with access token"""
        
        # Check rate limiting
        is_limited = await rate_limiter.is_rate_limited(
            identifier=client_ip,
            endpoint="login",
            max_attempts=5,
            window_minutes=1
        )
        
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Find user by email
        user = self.db.query(User).filter(User.email == login_data.email).first()
        
        if not user or not security_utils.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security_utils.create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        # Create session in Redis
        await session_manager.create_session(
            user_id=user.id,
            token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Reset rate limit on successful login
        await rate_limiter.reset_rate_limit(client_ip, "login")
        
        return (
            UserResponse.from_orm(user), 
            access_token, 
            settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def logout_user(self, user_id: uuid.UUID, token: str) -> None:
        """Logout user by invalidating session and blacklisting token"""
        
        # Invalidate session
        await session_manager.invalidate_session(user_id, token)
        
        # Add token to blacklist
        await token_blacklist.blacklist_token(
            token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def initiate_password_reset(
        self, 
        reset_data: ForgotPasswordRequest,
        client_ip: str
    ) -> str:
        """Initiate password reset process"""
        
        # Check rate limiting for password reset
        is_limited = await rate_limiter.is_rate_limited(
            identifier=client_ip,
            endpoint="forgot_password",
            max_attempts=3,
            window_minutes=5
        )
        
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset attempts. Please try again later."
            )
        
        # Find user by email
        user = self.db.query(User).filter(User.email == reset_data.email).first()
        
        # Always return success message (no user enumeration)
        success_message = "If an account exists, password reset instructions have been sent."
        
        if user and user.is_active:
            # Generate reset token
            reset_token = security_utils.generate_reset_token()
            reset_expires = datetime.utcnow() + timedelta(minutes=15)
            
            # Save reset token
            user.reset_token = reset_token
            user.reset_token_expires = reset_expires
            self.db.commit()
            
            # TODO: Send password reset email
            # await self.send_password_reset_email(user.email, reset_token)
        
        return success_message
    
    async def reset_password(self, reset_data: ResetPasswordRequest) -> str:
        """Reset user password using reset token"""
        
        # Find user by reset token
        user = self.db.query(User).filter(
            User.reset_token == reset_data.token,
            User.reset_token_expires > datetime.utcnow(),
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Hash new password
        new_password_hash = security_utils.hash_password(reset_data.password)
        
        # Update password and clear reset token
        user.password_hash = new_password_hash
        user.reset_token = None
        user.reset_token_expires = None
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Invalidate all existing sessions for this user
        await session_manager.invalidate_all_sessions(user.id)
        
        return "Password successfully reset"
    
    def get_user_profile(self, user_id: uuid.UUID) -> UserResponse:
        """Get user profile by ID"""
        
        user = self.db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
    
    def update_user_profile(
        self, 
        user_id: uuid.UUID, 
        update_data: UpdateProfileRequest
    ) -> UserResponse:
        """Update user profile"""
        
        user = self.db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        if update_data.name is not None:
            user.name = update_data.name
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return UserResponse.from_orm(user)
    
    def verify_email(self, verification_token: str) -> str:
        """Verify user email using verification token"""
        
        user = self.db.query(User).filter(
            User.verification_token == verification_token,
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Mark email as verified
        user.email_verified = True
        user.verification_token = None  # Clear the token
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return "Email successfully verified"
    
    async def deactivate_user(self, user_id: uuid.UUID) -> str:
        """Deactivate user account"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Deactivate user
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Invalidate all sessions
        await session_manager.invalidate_all_sessions(user_id)
        
        return "Account successfully deactivated"


def get_auth_service(db: Session) -> AuthService:
    """Dependency function to get AuthService instance"""
    return AuthService(db)
