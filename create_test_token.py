#!/usr/bin/env python3
"""
Authentication helper for OOUX ORCA development testing
Creates test users and generates JWT tokens for API testing
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.core.security import SecurityUtils
from app.core.database import get_db
from app.models import User
from sqlalchemy.orm import Session


def create_test_token(user_id: str, email: str = "test@example.com") -> str:
    """Create a test JWT token for development"""
    security = SecurityUtils()
    
    # Create token data
    token_data = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "iat": datetime.utcnow(),
    }
    
    # Create token that expires in 24 hours
    expires_delta = timedelta(hours=24)
    token = security.create_access_token(token_data, expires_delta)
    
    return token


def main():
    """Generate test authentication token"""
    # Generate a test user ID
    test_user_id = str(uuid.uuid4())
    test_email = "demo@ooux.dev"
    
    # Create token
    token = create_test_token(test_user_id, test_email)
    
    print("🔐 OOUX ORCA Development Authentication")
    print("=" * 50)
    print(f"Test User ID: {test_user_id}")
    print(f"Test Email: {test_email}")
    print(f"JWT Token: {token}")
    print()
    print("📋 Usage Instructions:")
    print("1. Copy the JWT token above")
    print("2. Add to your API requests as Authorization header:")
    print(f"   Authorization: Bearer {token}")
    print()
    print("🌐 Test with curl:")
    print(f'curl -H "Authorization: Bearer {token}" \\')
    print('     http://localhost:8000/api/v1/projects/demo-id/cta-matrix')
    print()
    print("⚠️  Note: This token is for development only!")
    print("   Real authentication requires user registration through /auth endpoints")


if __name__ == "__main__":
    main()
