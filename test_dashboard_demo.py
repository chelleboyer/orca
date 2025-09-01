#!/usr/bin/env python3
"""
Dashboard Demo Script
This script demonstrates how to use the OOUX ORCA dashboard by:
1. Creating a test user
2. Creating a test project
3. Adding the user to the project
4. Showing how to access the dashboard
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def main():
    print("🚀 OOUX ORCA Dashboard Demo")
    print("=" * 50)
    
    # Test data
    user_data = {
        "email": "demo@example.com",
        "password": "DemoPass123!",
        "name": "Demo User"
    }
    
    project_data = {
        "title": "Demo OOUX Project",
        "description": "A demonstration project showing the OOUX methodology dashboard",
        "slug": "demo-ooux-project"
    }
    
    try:
        # Step 1: Register user (or try to login if already exists)
        print("\n1. 👤 Setting up demo user...")
        
        # Try to register
        reg_response = requests.post(f"{API_BASE}/auth/register", json=user_data)
        
        if reg_response.status_code == 201:
            print("   ✅ Demo user registered successfully")
        elif reg_response.status_code == 400:
            print("   ℹ️  Demo user already exists, will try to login")
        else:
            print(f"   ❌ Registration failed: {reg_response.status_code}")
            return
        
        # Step 2: Login to get access token
        print("\n2. 🔐 Logging in...")
        login_response = requests.post(f"{API_BASE}/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        if login_response.status_code != 200:
            print(f"   ❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        print("   ✅ Login successful")
        
        # Headers for authenticated requests
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 3: Create a demo project
        print("\n3. 📁 Creating demo project...")
        project_response = requests.post(f"{API_BASE}/projects", json=project_data, headers=headers)
        
        if project_response.status_code == 201:
            project = project_response.json()
            project_id = project["id"]
            print(f"   ✅ Project created: {project['title']}")
            print(f"   📋 Project ID: {project_id}")
        else:
            print(f"   ❌ Project creation failed: {project_response.status_code}")
            print(f"   Response: {project_response.text}")
            return
        
        # Step 4: Get dashboard data
        print("\n4. 📊 Fetching dashboard data...")
        dashboard_response = requests.get(f"{API_BASE}/projects/{project_id}/dashboard", headers=headers)
        
        if dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            print("   ✅ Dashboard data retrieved successfully")
            
            # Display some dashboard info
            print(f"\n📈 Dashboard Overview:")
            print(f"   Project: {dashboard_data['project']['title']}")
            print(f"   Your Role: {dashboard_data['current_user_role']}")
            print(f"   Team Members: {len(dashboard_data['team_members'])}")
            print(f"   Recent Activities: {len(dashboard_data['recent_activity'])}")
            
            # Show OOUX progress
            print(f"\n🎯 OOUX Methodology Progress:")
            for section_id, section in dashboard_data['orca_progress'].items():
                section_name = section_id.replace('_', ' ').title()
                status_emoji = "✅" if section['status'] == 'complete' else "🚧" if section['status'] == 'in_progress' else "⭕"
                print(f"   {status_emoji} {section_name}: {section['progress_percentage']}% ({section['artifact_count']} artifacts)")
        
        else:
            print(f"   ❌ Dashboard fetch failed: {dashboard_response.status_code}")
            print(f"   Response: {dashboard_response.text}")
            return
        
        # Step 5: Instructions for accessing the web dashboard
        print("\n" + "=" * 50)
        print("🌐 HOW TO ACCESS THE DASHBOARD:")
        print("=" * 50)
        print(f"1. Open your browser to: {BASE_URL}")
        print("2. Since there's no login page UI yet, you can:")
        print("   a) Use the API directly (as shown above)")
        print(f"   b) Access dashboard JSON: {BASE_URL}/api/v1/projects/{project_id}/dashboard")
        print(f"   c) View API docs: {BASE_URL}/docs")
        print("\n📋 For the dashboard template demo:")
        print(f"   • Project ID: {project_id}")
        print(f"   • Access Token: {access_token[:20]}...")
        
        # Step 6: Create a simple test HTML page
        create_test_dashboard_page(project_id, access_token)
        
        print("\n🎉 Demo setup complete!")
        print("The OOUX ORCA application is ready for dashboard testing!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the application.")
        print("Make sure the server is running with: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

def create_test_dashboard_page(project_id, access_token):
    """Create a simple test HTML page to demonstrate the dashboard"""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OOUX ORCA Dashboard Demo</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f0f9ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .section {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
        .btn {{ background: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
        .btn:hover {{ background: #2563eb; }}
        pre {{ background: #f8fafc; padding: 15px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 OOUX ORCA Dashboard Demo</h1>
        <p>This page demonstrates how to interact with the OOUX ORCA dashboard API.</p>
    </div>
    
    <div class="section">
        <h2>📊 Dashboard Data</h2>
        <p>Click the button below to fetch live dashboard data:</p>
        <button class="btn" onclick="fetchDashboard()">Load Dashboard Data</button>
        <div id="dashboard-content"></div>
    </div>
    
    <div class="section">
        <h2>📋 Project Information</h2>
        <p><strong>Project ID:</strong> {project_id}</p>
        <p><strong>API Endpoint:</strong> /api/v1/projects/{project_id}/dashboard</p>
    </div>
    
    <script>
        const projectId = '{project_id}';
        const accessToken = '{access_token}';
        
        async function fetchDashboard() {{
            try {{
                const response = await fetch(`/api/v1/projects/${{projectId}}/dashboard`, {{
                    headers: {{
                        'Authorization': `Bearer ${{accessToken}}`
                    }}
                }});
                
                if (response.ok) {{
                    const data = await response.json();
                    document.getElementById('dashboard-content').innerHTML = `
                        <h3>✅ Dashboard Loaded Successfully!</h3>
                        <pre>${{JSON.stringify(data, null, 2)}}</pre>
                    `;
                }} else {{
                    document.getElementById('dashboard-content').innerHTML = `
                        <h3>❌ Error loading dashboard</h3>
                        <p>Status: ${{response.status}}</p>
                    `;
                }}
            }} catch (error) {{
                document.getElementById('dashboard-content').innerHTML = `
                    <h3>❌ Error: ${{error.message}}</h3>
                `;
            }}
        }}
    </script>
</body>
</html>"""
    
    with open("/home/michelle/PROJECTS/ooux/orca/dashboard_demo.html", "w") as f:
        f.write(html_content)
    
    print(f"\n📄 Created test page: dashboard_demo.html")
    print(f"   Open in browser: {BASE_URL}/dashboard_demo.html")

if __name__ == "__main__":
    main()
