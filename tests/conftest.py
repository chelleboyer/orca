"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis

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
    """Create test client with database override"""
    def override_get_db_with_session():
        yield db_session
    
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
