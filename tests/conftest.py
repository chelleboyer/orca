"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis
from unittest.mock import AsyncMock, patch

from app.main import app
from app.core.config import settings
from app.core.database import get_db, Base
from app.models.user import User
from app.core.security import security_utils


# Test database engine
engine = create_engine(settings.TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test Redis client
test_redis_client = None


async def get_test_redis():
    """Get test Redis client"""
    global test_redis_client
    if test_redis_client is None:
        test_redis_client = redis.from_url("redis://localhost:6379/1", decode_responses=True)
    return test_redis_client


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_engine():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for each test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override and Redis mocking"""
    def override_get_db_with_session():
        yield db_session
    
    # Mock Redis to avoid event loop issues
    with patch('app.core.security.get_redis_client') as mock_redis_func:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        mock_redis.keys.return_value = []
        mock_redis.setex.return_value = True
        mock_redis_func.return_value = mock_redis
        
        # Mock session validation to always return True for tests
        with patch('app.core.security.session_manager.validate_session', return_value=True):
            app.dependency_overrides[get_db] = override_get_db_with_session
            
            with TestClient(app) as test_client:
                yield test_client
                
            app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "TestPass123"
    }


@pytest.fixture
def sample_user(db_session, sample_user_data):
    """Create a sample user in the database"""
    password_hash = security_utils.hash_password(sample_user_data["password"])
    user = User(
        email=sample_user_data["email"],
        name=sample_user_data["name"],
        password_hash=password_hash,
        is_active=True,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_project(db_session, sample_user):
    """Create a sample project in the database"""
    from app.models.project import Project, ProjectMember
    
    project = Project(
        title="Test Project",
        description="A test project for OOUX",
        slug="test-project",
        created_by=sample_user.id,
        status="active"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    
    # Add user as project member with facilitator role
    membership = ProjectMember(
        project_id=project.id,
        user_id=sample_user.id,
        role="facilitator",
        status="active"
    )
    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)
    
    return project


@pytest.fixture
def auth_headers(sample_user):
    """Create authorization headers with JWT token"""
    token = security_utils.create_access_token(
        data={"sub": str(sample_user.id), "email": sample_user.email}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
async def redis_client():
    """Create test Redis client"""
    client = await get_test_redis()
    # Clear test database before each test
    await client.flushdb()
    yield client
    # Clean up after test
    await client.flushdb()
    await client.close()
