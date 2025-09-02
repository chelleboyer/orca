#!/usr/bin/env python3
"""
🎯 OOUX ORCA CTA Matrix - Quick Start Guide
Simple startup script for testing the CTA Matrix implementation
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required services are available"""
    print("🔍 Checking dependencies...")
    
    # Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("❌ Error: Please run this from the OOUX ORCA project root directory")
        print("   Current directory:", os.getcwd())
        return False
    
    # Check Python packages
    try:
        import uvicorn
        import fastapi
        print("✅ Python dependencies OK")
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def start_database_services():
    """Start PostgreSQL and Redis via Docker"""
    print("🐳 Starting database services...")
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d", "postgres", "redis"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ Database services started")
            return True
        else:
            print("⚠️  Database services may already be running")
            return True
    except subprocess.TimeoutExpired:
        print("⚠️  Docker startup timed out, but continuing...")
        return True
    except FileNotFoundError:
        print("⚠️  Docker not found - CTA Matrix will use mock data")
        return True
    except Exception as e:
        print(f"⚠️  Database service warning: {e}")
        return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting OOUX ORCA server...")
    try:
        # Import here to avoid issues if dependencies aren't installed
        import uvicorn
        from app.main import app
        
        # Start server in a way that doesn't block
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

def main():
    """Main startup sequence"""
    print("🎯 OOUX ORCA CTA Matrix - Quick Start")
    print("=" * 50)
    
    # Check if everything is ready
    if not check_dependencies():
        sys.exit(1)
    
    # Start services
    start_database_services()
    
    print("\n📋 What's available:")
    print("   🌐 Test Guide:     http://localhost:8000/api/v1/test-guide")
    print("   🎯 Demo Matrix:    http://localhost:8000/api/v1/demo/cta-matrix")
    print("   📚 API Docs:       http://localhost:8000/docs")
    print("   🏥 Health Check:   http://localhost:8000/health")
    
    print("\n🚀 Starting server...")
    print("   Press Ctrl+C to stop")
    print("   The browser will open automatically in 3 seconds...")
    
    # Start server (this will block)
    try:
        # Give a moment for user to read
        time.sleep(3)
        
        # Try to open browser
        try:
            webbrowser.open("http://localhost:8000/api/v1/test-guide")
        except:
            pass
        
        start_server()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
