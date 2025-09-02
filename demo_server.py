#!/usr/bin/env python3
"""
Demo server for Epic 4.2 CTA Matrix
Run this to see the CTA Matrix interface in action
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 Starting OOUX ORCA Demo Server")
    print("📍 CTA Matrix available at: http://localhost:8000/api/v1/projects/demo/cta-matrix")
    print("📍 Health check: http://localhost:8000/health")
    print("📍 API docs: http://localhost:8000/docs")
    print("\n🎯 Epic 4.2 CTA Matrix Features:")
    print("   • Interactive role-object matrix grid")
    print("   • HTMX-powered real-time updates") 
    print("   • Responsive design for all devices")
    print("   • Modal dialogs for CTA editing")
    print("   • Filtering and bulk operations")
    print("\n⚠️  Note: Authentication required for full functionality")
    print("💡 Use test credentials or create account via API")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
