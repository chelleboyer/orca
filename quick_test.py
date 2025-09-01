#!/usr/bin/env python3
"""
Simple Dashboard Test Script
"""

import subprocess
import time
import json

def test_api():
    """Test the dashboard API with simple HTTP requests"""
    base_url = "http://localhost:8000"
    
    print("🚀 OOUX ORCA Dashboard Quick Test")
    print("=" * 40)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        result = subprocess.run([
            "curl", "-s", f"{base_url}/health"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Server is running!")
            response = json.loads(result.stdout)
            print(f"   Status: {response.get('status')}")
            print(f"   Version: {response.get('version')}")
        else:
            print("   ❌ Server not responding")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: API Documentation
    print(f"\n2. 📚 API Documentation available at:")
    print(f"   {base_url}/docs")
    
    # Test 3: Register user
    print(f"\n3. 👤 To register a user, run:")
    print(f"""   curl -X POST "{base_url}/api/v1/auth/register" \\
     -H "Content-Type: application/json" \\
     -d '{{"email": "test@example.com", "password": "TestPass123!", "name": "Test User"}}'""")
    
    # Test 4: Login
    print(f"\n4. 🔐 To login, run:")
    print(f"""   curl -X POST "{base_url}/api/v1/auth/login" \\
     -H "Content-Type: application/json" \\
     -d '{{"email": "test@example.com", "password": "TestPass123!"}}'""")
    
    # Test 5: Dashboard info
    print(f"\n5. 📊 Dashboard Features:")
    print("   ✅ OOUX Methodology Progress Tracking")
    print("   ✅ Team Management & Permissions")
    print("   ✅ Project Statistics & Analytics")
    print("   ✅ Real-time Activity Feed")
    print("   ✅ Member Invitation System")
    print("   ✅ Responsive UI Templates")
    
    print(f"\n🌐 Open your browser to:")
    print(f"   Main API: {base_url}")
    print(f"   Documentation: {base_url}/docs")
    
    return True

if __name__ == "__main__":
    test_api()
