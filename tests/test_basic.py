"""
Test basic application functionality
"""

def test_imports():
    """Test that all main modules can be imported"""
    try:
        from app.core.config import settings
        from app.core.database import Base
        from app.main import app
        print("✅ All imports successful")
        print(f"✅ App: {app.title}")
        print(f"✅ Config: {settings.APP_NAME}")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_health_endpoint():
    """Test the health endpoint"""
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint working")
        return True
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running basic application tests...")
    
    import_success = test_imports()
    if not import_success:
        exit(1)
    
    # Install test client dependency
    try:
        import httpx
    except ImportError:
        print("Installing httpx for testing...")
        import subprocess
        subprocess.check_call(["/home/michelle/PROJECTS/ooux/orca/.venv/bin/pip", "install", "httpx"])
    
    health_success = test_health_endpoint()
    if not health_success:
        exit(1)
    
    print("\n🎉 All tests passed! Application is ready for development.")
