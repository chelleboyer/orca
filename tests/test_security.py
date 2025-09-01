"""
Security tests for authentication system
"""

import pytest
import time
from unittest.mock import patch

from app.core.security import security_utils, SessionManager, RateLimiter, TokenBlacklist
from app.schemas.auth import UserRegister


class TestSecurityUtils:
    """Test cases for security utilities"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123"
        
        # Hash password
        hashed = security_utils.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # Argon2 hashes are typically long
        
        # Verify correct password
        assert security_utils.verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert security_utils.verify_password("WrongPassword", hashed) is False
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        data = {"sub": "user123", "email": "test@example.com"}
        
        # Create token
        token = security_utils.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long
        
        # Verify token
        payload = security_utils.verify_token(token)
        
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]
        assert "exp" in payload
    
    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        from datetime import timedelta
        
        data = {"sub": "user123"}
        
        # Create token with very short expiration
        token = security_utils.create_access_token(
            data, 
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid immediately
        payload = security_utils.verify_token(token)
        assert payload["sub"] == data["sub"]
        
        # Wait for token to expire
        time.sleep(2)
        
        # Token should now be invalid
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            security_utils.verify_token(token)
        
        assert exc_info.value.status_code == 401
    
    def test_invalid_jwt_token(self):
        """Test verification of invalid JWT token"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            security_utils.verify_token("invalid_token")
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
    
    def test_generate_tokens(self):
        """Test generation of secure tokens"""
        reset_token = security_utils.generate_reset_token()
        verification_token = security_utils.generate_verification_token()
        
        assert len(reset_token) > 30
        assert len(verification_token) > 30
        assert reset_token != verification_token
        
        # Tokens should be URL-safe
        import string
        allowed_chars = string.ascii_letters + string.digits + '-_'
        assert all(c in allowed_chars for c in reset_token)
        assert all(c in allowed_chars for c in verification_token)


class TestPasswordValidation:
    """Test cases for password validation in schemas"""
    
    def test_valid_passwords(self):
        """Test validation of valid passwords"""
        valid_passwords = [
            "Password123",
            "MySecurePass1",
            "Test123Password",
            "Abc123defG",
        ]
        
        for password in valid_passwords:
            user_data = UserRegister(
                email="test@example.com",
                name="Test User",
                password=password
            )
            assert user_data.password == password
    
    def test_invalid_passwords(self):
        """Test validation of invalid passwords"""
        from pydantic import ValidationError
        
        invalid_passwords = [
            "short",                    # Too short
            "password123",              # No uppercase
            "PASSWORD123",              # No lowercase
            "PasswordABC",              # No number
            "Pass123",                  # Too short
        ]
        
        for password in invalid_passwords:
            with pytest.raises(ValidationError):
                UserRegister(
                    email="test@example.com",
                    name="Test User",
                    password=password
                )


class TestRateLimiting:
    """Test cases for rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_basic(self):
        """Test basic rate limiting functionality"""
        with patch('app.core.security.get_redis_client') as mock_redis:
            # Mock Redis client
            mock_client = mock_redis.return_value
            mock_client.get.return_value = None  # First request
            mock_client.setex.return_value = None
            mock_client.incr.return_value = None
            
            rate_limiter = RateLimiter()
            
            # First request should not be rate limited
            is_limited = await rate_limiter.is_rate_limited(
                "127.0.0.1", 
                "login", 
                max_attempts=3, 
                window_minutes=1
            )
            
            assert is_limited is False
    
    @pytest.mark.asyncio
    async def test_rate_limiting_exceeded(self):
        """Test rate limiting when limit is exceeded"""
        with patch('app.core.security.get_redis_client') as mock_redis:
            # Mock Redis client returning max attempts reached
            mock_client = mock_redis.return_value
            mock_client.get.return_value = "3"  # Max attempts reached
            
            rate_limiter = RateLimiter()
            
            is_limited = await rate_limiter.is_rate_limited(
                "127.0.0.1", 
                "login", 
                max_attempts=3, 
                window_minutes=1
            )
            
            assert is_limited is True


class TestSessionManagement:
    """Test cases for session management"""
    
    @pytest.mark.asyncio
    async def test_session_creation_and_validation(self):
        """Test session creation and validation"""
        with patch('app.core.security.get_redis_client') as mock_redis:
            import uuid
            
            mock_client = mock_redis.return_value
            mock_client.setex.return_value = None
            mock_client.get.return_value = "active"
            
            session_manager = SessionManager()
            user_id = uuid.uuid4()
            token = "sample_token"
            
            # Create session
            await session_manager.create_session(user_id, token)
            
            # Validate session
            is_valid = await session_manager.validate_session(user_id, token)
            
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_session_invalidation(self):
        """Test session invalidation"""
        with patch('app.core.security.get_redis_client') as mock_redis:
            import uuid
            
            mock_client = mock_redis.return_value
            mock_client.delete.return_value = None
            mock_client.keys.return_value = ["session:user123:token1", "session:user123:token2"]
            
            session_manager = SessionManager()
            user_id = uuid.uuid4()
            
            # Test single session invalidation
            await session_manager.invalidate_session(user_id, "token1")
            mock_client.delete.assert_called()
            
            # Test all sessions invalidation
            await session_manager.invalidate_all_sessions(user_id)
            mock_client.keys.assert_called()


class TestTokenBlacklist:
    """Test cases for token blacklisting"""
    
    @pytest.mark.asyncio
    async def test_token_blacklisting(self):
        """Test token blacklisting functionality"""
        with patch('app.core.security.get_redis_client') as mock_redis:
            mock_client = mock_redis.return_value
            mock_client.setex.return_value = None
            mock_client.get.return_value = "blacklisted"
            
            blacklist = TokenBlacklist()
            token = "sample_token"
            
            # Blacklist token
            await blacklist.blacklist_token(token, 3600)
            
            # Check if blacklisted
            is_blacklisted = await blacklist.is_blacklisted(token)
            
            assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_token_not_blacklisted(self):
        """Test checking non-blacklisted token"""
        with patch('app.core.security.get_redis_client') as mock_redis:
            mock_client = mock_redis.return_value
            mock_client.get.return_value = None  # Not blacklisted
            
            blacklist = TokenBlacklist()
            token = "clean_token"
            
            is_blacklisted = await blacklist.is_blacklisted(token)
            
            assert is_blacklisted is False
