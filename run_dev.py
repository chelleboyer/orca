#!/usr/bin/env python3
"""
Development server script for OOUX ORCA Project Builder
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ["PYTHONPATH"] = str(project_root)

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    from app.core.config import settings
    
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🏥 Health check: http://localhost:8000/health")
    print("---")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )
