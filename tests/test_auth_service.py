"""
Unit tests for authentication service
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, UpdateProfileRequest
from app.core.security import security_utils


class TestAuthService:
    """Test cases for AuthService"""
    
    def test_register_user_success(self, db_session: Session):
        """Test successful user registration"""
        auth_service = AuthService(db_session)
        user_data = UserRegister(
            email="newuser@example.com",
            name="New User",
            password="NewPass123"
        )
        
        result = asyncio.run(auth_service.register_user(user_data))
        
        assert result.email == user_data.email
        assert result.name == user_data.name
        assert result.is_active is True
        assert result.email_verified is False
        
        # Verify user exists in database
        db_user = db_session.query(User).filter(User.email == user_data.email).first()
        assert db_user is not None
        assert security_utils.verify_password(user_data.password, db_user.password_hash)
    
    def test_register_user_duplicate_email(self, db_session: Session, sample_user: User):
        """Test registration with duplicate email"""
        auth_service = AuthService(db_session)
        user_data = UserRegister(
            email=sample_user.email,
            name="Another User",
            password="AnotherPass123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(auth_service.register_user(user_data))
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail
    
    @patch('app.services.auth_service.rate_limiter.is_rate_limited')
    @patch('app.services.auth_service.session_manager.create_session')
    @patch('app.services.auth_service.rate_limiter.reset_rate_limit')
    async def test_authenticate_user_success(
        self, 
        mock_reset_rate_limit,
        mock_create_session,
        mock_is_rate_limited,
        db_session: Session, 
        sample_user: User,
        sample_user_data: dict
    ):
        """Test successful user authentication"""
        mock_is_rate_limited.return_value = False
        mock_create_session.return_value = None
        mock_reset_rate_limit.return_value = None
        
        auth_service = AuthService(db_session)
        login_data = UserLogin(
            email=sample_user_data["email"],
            password=sample_user_data["password"]
        )
        
        user, token, expires_in = await auth_service.authenticate_user(login_data, "127.0.0.1")
        
        assert user.email == sample_user.email
        assert user.name == sample_user.name
        assert token is not None
        assert expires_in > 0
        
        # Verify last_login was updated
        db_session.refresh(sample_user)
        assert sample_user.last_login is not None
    
    @patch('app.services.auth_service.rate_limiter.is_rate_limited')
    async def test_authenticate_user_rate_limited(
        self, 
        mock_is_rate_limited,
        db_session: Session
    ):
        """Test authentication with rate limiting"""
        mock_is_rate_limited.return_value = True
        
        auth_service = AuthService(db_session)
        login_data = UserLogin(
            email="test@example.com",
            password="TestPass123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(login_data, "127.0.0.1")
        
        assert exc_info.value.status_code == 429
        assert "Too many login attempts" in exc_info.value.detail
    
    def test_authenticate_user_invalid_credentials(self, db_session: Session, sample_user: User):
        """Test authentication with invalid credentials"""
        auth_service = AuthService(db_session)
        login_data = UserLogin(
            email=sample_user.email,
            password="WrongPassword"
        )
        
        with patch('app.services.auth_service.rate_limiter.is_rate_limited', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(auth_service.authenticate_user(login_data, "127.0.0.1"))
        
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in exc_info.value.detail
    
    def test_authenticate_user_inactive_account(self, db_session: Session, sample_user: User, sample_user_data: dict):
        """Test authentication with inactive account"""
        # Deactivate user
        sample_user.is_active = False
        db_session.commit()
        
        auth_service = AuthService(db_session)
        login_data = UserLogin(
            email=sample_user_data["email"],
            password=sample_user_data["password"]
        )
        
        with patch('app.services.auth_service.rate_limiter.is_rate_limited', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(auth_service.authenticate_user(login_data, "127.0.0.1"))
        
        assert exc_info.value.status_code == 401
        assert "Account is disabled" in exc_info.value.detail
    
    @patch('app.services.auth_service.session_manager.invalidate_session')
    @patch('app.services.auth_service.token_blacklist.blacklist_token')
    async def test_logout_user(
        self,
        mock_blacklist_token,
        mock_invalidate_session,
        db_session: Session
    ):
        """Test user logout"""
        mock_invalidate_session.return_value = None
        mock_blacklist_token.return_value = None
        
        auth_service = AuthService(db_session)
        user_id = uuid.uuid4()
        token = "sample_token"
        
        await auth_service.logout_user(user_id, token)
        
        mock_invalidate_session.assert_called_once_with(user_id, token)
        mock_blacklist_token.assert_called_once()
    
    @patch('app.services.auth_service.rate_limiter.is_rate_limited')
    async def test_initiate_password_reset_success(
        self,
        mock_is_rate_limited,
        db_session: Session,
        sample_user: User
    ):
        """Test successful password reset initiation"""
        mock_is_rate_limited.return_value = False
        
        auth_service = AuthService(db_session)
        reset_data = ForgotPasswordRequest(email=sample_user.email)
        
        result = await auth_service.initiate_password_reset(reset_data, "127.0.0.1")
        
        assert "password reset instructions" in result
        
        # Verify reset token was set
        db_session.refresh(sample_user)
        assert sample_user.reset_token is not None
        assert sample_user.reset_token_expires is not None
    
    @patch('app.services.auth_service.rate_limiter.is_rate_limited')
    async def test_initiate_password_reset_rate_limited(
        self,
        mock_is_rate_limited,
        db_session: Session
    ):
        """Test password reset with rate limiting"""
        mock_is_rate_limited.return_value = True
        
        auth_service = AuthService(db_session)
        reset_data = ForgotPasswordRequest(email="test@example.com")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.initiate_password_reset(reset_data, "127.0.0.1")
        
        assert exc_info.value.status_code == 429
    
    @patch('app.services.auth_service.session_manager.invalidate_all_sessions')
    async def test_reset_password_success(
        self,
        mock_invalidate_sessions,
        db_session: Session,
        sample_user: User
    ):
        """Test successful password reset"""
        mock_invalidate_sessions.return_value = None
        
        # Set up reset token
        reset_token = "valid_reset_token"
        sample_user.reset_token = reset_token
        sample_user.reset_token_expires = datetime.utcnow() + timedelta(minutes=15)
        db_session.commit()
        
        auth_service = AuthService(db_session)
        reset_data = ResetPasswordRequest(
            token=reset_token,
            password="NewPassword123"
        )
        
        result = await auth_service.reset_password(reset_data)
        
        assert "successfully reset" in result
        
        # Verify password was changed and token cleared
        db_session.refresh(sample_user)
        assert sample_user.reset_token is None
        assert sample_user.reset_token_expires is None
        assert security_utils.verify_password("NewPassword123", sample_user.password_hash)
    
    def test_reset_password_invalid_token(self, db_session: Session):
        """Test password reset with invalid token"""
        auth_service = AuthService(db_session)
        reset_data = ResetPasswordRequest(
            token="invalid_token",
            password="NewPassword123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(auth_service.reset_password(reset_data))
        
        assert exc_info.value.status_code == 400
        assert "Invalid or expired" in exc_info.value.detail
    
    def test_get_user_profile_success(self, db_session: Session, sample_user: User):
        """Test successful user profile retrieval"""
        auth_service = AuthService(db_session)
        
        result = auth_service.get_user_profile(sample_user.id)
        
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.name == sample_user.name
    
    def test_get_user_profile_not_found(self, db_session: Session):
        """Test user profile retrieval for non-existent user"""
        auth_service = AuthService(db_session)
        non_existent_id = uuid.uuid4()
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.get_user_profile(non_existent_id)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail
    
    def test_update_user_profile_success(self, db_session: Session, sample_user: User):
        """Test successful user profile update"""
        auth_service = AuthService(db_session)
        update_data = UpdateProfileRequest(name="Updated Name")
        
        result = auth_service.update_user_profile(sample_user.id, update_data)
        
        assert result.name == "Updated Name"
        
        # Verify database was updated
        db_session.refresh(sample_user)
        assert sample_user.name == "Updated Name"
    
    def test_verify_email_success(self, db_session: Session, sample_user: User):
        """Test successful email verification"""
        # Set up verification token
        verification_token = "valid_verification_token"
        sample_user.verification_token = verification_token
        sample_user.email_verified = False
        db_session.commit()
        
        auth_service = AuthService(db_session)
        
        result = auth_service.verify_email(verification_token)
        
        assert "successfully verified" in result
        
        # Verify email was marked as verified and token cleared
        db_session.refresh(sample_user)
        assert sample_user.email_verified is True
        assert sample_user.verification_token is None
    
    def test_verify_email_invalid_token(self, db_session: Session):
        """Test email verification with invalid token"""
        auth_service = AuthService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_email("invalid_token")
        
        assert exc_info.value.status_code == 400
        assert "Invalid verification token" in exc_info.value.detail
    
    @patch('app.services.auth_service.session_manager.invalidate_all_sessions')
    async def test_deactivate_user_success(
        self,
        mock_invalidate_sessions,
        db_session: Session,
        sample_user: User
    ):
        """Test successful user deactivation"""
        mock_invalidate_sessions.return_value = None
        
        auth_service = AuthService(db_session)
        
        result = await auth_service.deactivate_user(sample_user.id)
        
        assert "successfully deactivated" in result
        
        # Verify user was deactivated
        db_session.refresh(sample_user)
        assert sample_user.is_active is False


# Import asyncio at the top if not already imported
import asyncio
