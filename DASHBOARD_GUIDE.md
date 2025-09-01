# How to Try the OOUX ORCA Dashboard

## 🚀 Quick Start Guide

The OOUX ORCA dashboard is now running! Here's how to access and test it:

### 1. Make sure the server is running
```bash
cd /home/michelle/PROJECTS/ooux/orca
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Test the API endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### View API Documentation
Open in browser: http://localhost:8000/docs

### 3. Register a Test User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "name": "Test User"
  }'
```

### 4. Login to Get Access Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com", 
    "password": "TestPass123!"
  }'
```

Save the `access_token` from the response!

### 5. Create a Test Project
```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "title": "My OOUX Project",
    "description": "A test project for the dashboard",
    "slug": "my-ooux-project"
  }'
```

Save the `id` from the response (this is your PROJECT_ID)!

### 6. Access the Dashboard
```bash
curl -X GET "http://localhost:8000/api/v1/projects/PROJECT_ID/dashboard" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### 7. View Dashboard in Browser

The dashboard JSON data will show:
- Project information and metadata
- Your role and permissions
- OOUX methodology progress (Object Catalog, NOM Matrix, etc.)
- Team members and their roles
- Recent project activity
- Project statistics

### 8. Dashboard Features Implemented

✅ **OOUX Methodology Progress Tracking**
- Object Catalog progress
- NOM (Nested Object Matrix) progress  
- CTA Matrix progress
- Object Map visualization
- CDLL (Content, Data, Links, Layout) specifications

✅ **Team Management**
- Member roles (Owner, Facilitator, Contributor, Viewer)
- Permission-based access control
- Member invitation system
- Activity tracking

✅ **Project Statistics**
- Object count
- Relationship count
- CTA count
- Attribute count
- Team size

✅ **Responsive Dashboard UI**
- Progress cards with visual indicators
- Team member cards with avatars
- Recent activity feed
- Project statistics widgets
- Member invitation modals

### 9. Frontend Templates

The dashboard templates are located in:
- `app/templates/dashboard/project_dashboard.html` - Main dashboard template
- `app/templates/app_base.html` - Base application template
- `app/static/css/dashboard.css` - Dashboard styling
- `app/static/js/dashboard.js` - Dashboard functionality

### 10. Next Steps

Once you have the API working, you can:
1. Create more projects
2. Invite team members
3. Track OOUX methodology progress
4. View the interactive dashboard UI
5. Test the real-time features

The dashboard provides a complete foundation for the OOUX methodology workflow!
