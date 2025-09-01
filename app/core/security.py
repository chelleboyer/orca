"""
Security utilities for JWT tokens, password hashing, and authentication
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Union
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import argon2
import redis.asyncio as redis

from app.core.config import settings


# Password hashing context using Argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,       # 3 iterations
    argon2__parallelism=1,     # Single thread
)

# HTTP Bearer token security
security = HTTPBearer()

# Redis client for session management
redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get Redis client for session management"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


class SecurityUtils:
    """Utility class for security operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using Argon2"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure random token for password reset"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure random token for email verification"""
        return secrets.token_urlsafe(32)


class SessionManager:
    """Manages user sessions in Redis"""
    
    def __init__(self):
        self.redis_client = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis client"""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    async def create_session(
        self, 
        user_id: uuid.UUID, 
        token: str, 
        expires_in: Optional[int] = None
    ) -> None:
        """Create a new user session"""
        redis_client = await self._get_redis()
        
        if expires_in is None:
            expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        
        session_key = f"session:{user_id}:{token}"
        await redis_client.setex(
            session_key,
            expires_in,
            "active"
        )
    
    async def validate_session(self, user_id: uuid.UUID, token: str) -> bool:
        """Validate if a session is active"""
        redis_client = await self._get_redis()
        session_key = f"session:{user_id}:{token}"
        
        result = await redis_client.get(session_key)
        return result is not None
    
    async def invalidate_session(self, user_id: uuid.UUID, token: str) -> None:
        """Invalidate a user session"""
        redis_client = await self._get_redis()
        session_key = f"session:{user_id}:{token}"
        await redis_client.delete(session_key)
    
    async def invalidate_all_sessions(self, user_id: uuid.UUID) -> None:
        """Invalidate all sessions for a user"""
        redis_client = await self._get_redis()
        pattern = f"session:{user_id}:*"
        
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)


class RateLimiter:
    """Rate limiting for authentication endpoints"""
    
    def __init__(self):
        self.redis_client = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis client"""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    async def is_rate_limited(
        self, 
        identifier: str, 
        endpoint: str, 
        max_attempts: int = 5,
        window_minutes: int = 1
    ) -> bool:
        """Check if an identifier is rate limited for an endpoint"""
        redis_client = await self._get_redis()
        
        key = f"rate_limit:{endpoint}:{identifier}"
        current_attempts = await redis_client.get(key)
        
        if current_attempts is None:
            # First attempt
            await redis_client.setex(key, window_minutes * 60, 1)
            return False
        
        if int(current_attempts) >= max_attempts:
            return True
        
        # Increment attempt count
        await redis_client.incr(key)
        return False
    
    async def reset_rate_limit(self, identifier: str, endpoint: str) -> None:
        """Reset rate limit for an identifier and endpoint"""
        redis_client = await self._get_redis()
        key = f"rate_limit:{endpoint}:{identifier}"
        await redis_client.delete(key)


# Global instances
security_utils = SecurityUtils()
session_manager = SessionManager()
rate_limiter = RateLimiter()


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current user from JWT token
    This is a basic version - will be enhanced when we have user service
    """
    token = credentials.credentials
    
    try:
        payload = security_utils.verify_token(token)
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate session is still active
        is_active = await session_manager.validate_session(
            uuid.UUID(user_id), 
            token
        )
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {"user_id": user_id, "token": token}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Token blacklist for logout functionality
class TokenBlacklist:
    """Manages blacklisted tokens"""
    
    def __init__(self):
        self.redis_client = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis client"""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    async def blacklist_token(self, token: str, expires_in: int) -> None:
        """Add token to blacklist"""
        redis_client = await self._get_redis()
        key = f"blacklist:{token}"
        await redis_client.setex(key, expires_in, "blacklisted")
    
    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        redis_client = await self._get_redis()
        key = f"blacklist:{token}"
        result = await redis_client.get(key)
        return result is not None


# Global token blacklist instance
token_blacklist = TokenBlacklist()
