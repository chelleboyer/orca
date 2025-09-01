"""
Pydantic schemas for authentication endpoints
"""

from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=50)

    @validator('name')
    def validate_name(cls, v):
        """Validate display name contains only alphanumeric characters and spaces"""
        if not re.match(r'^[a-zA-Z0-9\s]+$', v.strip()):
            raise ValueError('Name must contain only alphanumeric characters and spaces')
        return v.strip()


class UserRegister(UserBase):
    """Schema for user registration request"""
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v


class UserLogin(BaseModel):
    """Schema for user login request"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response (public data only)"""
    id: uuid.UUID
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    email_verified: bool

    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    """Schema for user profile with additional details"""
    pass


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LoginResponse(TokenResponse):
    """Schema for login response"""
    pass


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset request"""
    token: str
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v


class UpdateProfileRequest(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)

    @validator('name')
    def validate_name(cls, v):
        """Validate display name contains only alphanumeric characters and spaces"""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9\s]+$', v.strip()):
                raise ValueError('Name must contain only alphanumeric characters and spaces')
            return v.strip()
        return v


class MessageResponse(BaseModel):
    """Schema for simple message responses"""
    message: str


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str


class ValidationErrorDetail(BaseModel):
    """Schema for validation error details"""
    loc: list
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses"""
    detail: list[ValidationErrorDetail]
