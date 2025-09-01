#!/usr/bin/env python3
"""
Quick compilation and setup verification script
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ["PYTHONPATH"] = str(project_root)

def check_imports():
    """Check all critical imports"""
    print("🔍 Checking imports...")
    
    try:
        # Core imports
        from app.core.config import settings
        print("  ✅ Config module")
        
        from app.core.database import Base, get_db
        print("  ✅ Database module")
        
        from app.main import app
        print("  ✅ FastAPI application")
        
        # Test FastAPI functionality
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        print("  ✅ Health endpoint")
        
        print(f"\n📋 Application: {app.title}")
        print(f"📋 Version: {settings.APP_VERSION}")
        print(f"📋 Environment: {settings.ENVIRONMENT}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def check_dependencies():
    """Check key dependencies"""
    print("\n🔍 Checking dependencies...")
    
    dependencies = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "pydantic_settings",
        "sqlalchemy",
        "jinja2",
        "httpx"
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - NOT INSTALLED")
            return False
    
    return True

def main():
    """Main verification function"""
    print("🧪 OOUX ORCA Project Builder - Compilation Check")
    print("=" * 50)
    
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\n❌ Dependency check failed!")
        return False
    
    imports_ok = check_imports()
    if not imports_ok:
        print("\n❌ Import check failed!")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 SUCCESS! Application compiles and runs correctly.")
    print("\n🚀 Ready to start development!")
    print("   Run: python run_dev.py")
    print("   Or:  uvicorn app.main:app --reload")
    print("\n📚 API Docs: http://localhost:8000/docs")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
