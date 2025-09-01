"""
Integration tests for authentication API endpoints
"""

import pytest
import json
from fastapi.testclient import TestClient

from app.models.user import User
from app.core.security import security_utils


class TestAuthEndpoints:
    """Test cases for authentication API endpoints"""
    
    def test_register_success(self, client: TestClient):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "name": "New User",
            "password": "TestPass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]
        assert "id" in data
        assert "created_at" in data
        assert data["is_active"] is True
        assert data["email_verified"] is False
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "name": "Test User",
            "password": "TestPass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
        assert "email" in response.text.lower()
    
    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password"""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "weak"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
        assert "password" in response.text.lower()
    
    def test_register_invalid_name(self, client: TestClient):
        """Test registration with invalid name"""
        user_data = {
            "email": "test@example.com",
            "name": "X",  # Too short
            "password": "TestPass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_register_duplicate_email(self, client: TestClient, sample_user: User):
        """Test registration with duplicate email"""
        user_data = {
            "email": sample_user.email,
            "name": "Another User",
            "password": "TestPass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"]
    
    def test_login_success(self, client: TestClient, sample_user: User, sample_user_data: dict):
        """Test successful user login"""
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == sample_user.email
    
    def test_login_invalid_credentials(self, client: TestClient, sample_user: User):
        """Test login with invalid credentials"""
        login_data = {
            "email": sample_user.email,
            "password": "WrongPassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Incorrect email or password" in data["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Incorrect email or password" in data["detail"]
    
    def test_login_inactive_user(self, client: TestClient, sample_user: User, sample_user_data: dict, db_session):
        """Test login with inactive user"""
        # Deactivate user
        sample_user.is_active = False
        db_session.commit()
        
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Account is disabled" in data["detail"]
    
    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Test successful user logout"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully logged out" in data["message"]
    
    def test_logout_without_token(self, client: TestClient):
        """Test logout without authentication token"""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 403  # HTTPBearer returns 403 for missing token
    
    def test_logout_invalid_token(self, client: TestClient):
        """Test logout with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        
        assert response.status_code == 401
    
    def test_forgot_password_success(self, client: TestClient, sample_user: User):
        """Test successful forgot password request"""
        reset_data = {"email": sample_user.email}
        
        response = client.post("/api/v1/auth/forgot-password", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "password reset instructions" in data["message"]
    
    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """Test forgot password with non-existent email"""
        reset_data = {"email": "nonexistent@example.com"}
        
        response = client.post("/api/v1/auth/forgot-password", json=reset_data)
        
        # Should return success message for security (no user enumeration)
        assert response.status_code == 200
        data = response.json()
        assert "password reset instructions" in data["message"]
    
    def test_forgot_password_invalid_email(self, client: TestClient):
        """Test forgot password with invalid email format"""
        reset_data = {"email": "invalid-email"}
        
        response = client.post("/api/v1/auth/forgot-password", json=reset_data)
        
        assert response.status_code == 422
    
    def test_reset_password_success(self, client: TestClient, sample_user: User, db_session):
        """Test successful password reset"""
        # Set up reset token
        reset_token = "valid_reset_token"
        sample_user.reset_token = reset_token
        from datetime import datetime, timedelta
        sample_user.reset_token_expires = datetime.utcnow() + timedelta(minutes=15)
        db_session.commit()
        
        reset_data = {
            "token": reset_token,
            "password": "NewPassword123"
        }
        
        response = client.post("/api/v1/auth/reset-password", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "successfully reset" in data["message"]
    
    def test_reset_password_invalid_token(self, client: TestClient):
        """Test password reset with invalid token"""
        reset_data = {
            "token": "invalid_token",
            "password": "NewPassword123"
        }
        
        response = client.post("/api/v1/auth/reset-password", json=reset_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired" in data["detail"]
    
    def test_reset_password_weak_password(self, client: TestClient):
        """Test password reset with weak password"""
        reset_data = {
            "token": "some_token",
            "password": "weak"
        }
        
        response = client.post("/api/v1/auth/reset-password", json=reset_data)
        
        assert response.status_code == 422
    
    def test_get_profile_success(self, client: TestClient, auth_headers: dict, sample_user: User):
        """Test successful profile retrieval"""
        response = client.get("/api/v1/auth/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user.email
        assert data["name"] == sample_user.name
        assert "id" in data
        assert "created_at" in data
    
    def test_get_profile_without_token(self, client: TestClient):
        """Test profile retrieval without authentication token"""
        response = client.get("/api/v1/auth/profile")
        
        assert response.status_code == 403  # HTTPBearer returns 403 for missing token
    
    def test_get_profile_invalid_token(self, client: TestClient):
        """Test profile retrieval with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/profile", headers=headers)
        
        assert response.status_code == 401
    
    def test_update_profile_success(self, client: TestClient, auth_headers: dict, sample_user: User):
        """Test successful profile update"""
        update_data = {"name": "Updated Name"}
        
        response = client.patch("/api/v1/auth/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
    
    def test_update_profile_invalid_name(self, client: TestClient, auth_headers: dict):
        """Test profile update with invalid name"""
        update_data = {"name": "X"}  # Too short
        
        response = client.patch("/api/v1/auth/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    def test_update_profile_without_token(self, client: TestClient):
        """Test profile update without authentication token"""
        update_data = {"name": "Updated Name"}
        
        response = client.patch("/api/v1/auth/profile", json=update_data)
        
        assert response.status_code == 403
    
    def test_verify_email_success(self, client: TestClient, sample_user: User, db_session):
        """Test successful email verification"""
        # Set up verification token
        verification_token = "valid_verification_token"
        sample_user.verification_token = verification_token
        sample_user.email_verified = False
        db_session.commit()
        
        response = client.post(f"/api/v1/auth/verify-email/{verification_token}")
        
        assert response.status_code == 200
        data = response.json()
        assert "successfully verified" in data["message"]
    
    def test_verify_email_invalid_token(self, client: TestClient):
        """Test email verification with invalid token"""
        response = client.post("/api/v1/auth/verify-email/invalid_token")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid verification token" in data["detail"]
    
    def test_api_documentation_accessible(self, client: TestClient):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/redoc")
        assert response.status_code == 200
