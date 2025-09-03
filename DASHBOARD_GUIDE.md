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
- Object Catalog progress (Epic 2 ✅ Complete)
- NOM (Nested Object Matrix) progress (Epic 3 ✅ Complete)
- CTA Matrix progress (Epic 4 ✅ Complete)  
- Attributes & Object Map visualization (Epic 5 ✅ Complete)
- **NOW/NEXT/LATER Prioritization** (Epic 6.1 ✅ **NEW - COMPLETE**)
- CDLL (Content, Data, Links, Layout) specifications (Epic 6.2-6.3 📋 Planned)

✅ **Team Management**
- Member roles (Owner, Facilitator, Contributor, Viewer)
- Permission-based access control
- Member invitation system
- Activity tracking

✅ **Project Statistics**
- Object count with definitions and synonyms
- Relationship count with cardinality mapping
- CTA count with role associations
- Attribute count with data types
- **Prioritization analytics** (Now/Next/Later distribution) **✅ NEW**
- Team size and activity metrics

✅ **Prioritization Features** **✅ NEW - Epic 6.1**
- Now/Next/Later phase management for all artifacts
- 1-10 scoring system with validation
- Bulk drag-and-drop operations
- Prioritization board view organized by phases
- Statistics and analytics dashboard
- Historical snapshots for version control
- Filtering by item type and priority phase

✅ **Responsive Dashboard UI**
- Progress cards with visual indicators
- Team member cards with avatars
- Recent activity feed
- Project statistics widgets
- Member invitation modals
- **Prioritization board interface** **✅ NEW**

### 9. Frontend Templates

The dashboard templates are located in:
- `app/templates/dashboard/project_dashboard.html` - Main dashboard template
- `app/templates/app_base.html` - Base application template
- `app/static/css/dashboard.css` - Dashboard styling
- `app/static/js/dashboard.js` - Dashboard functionality

### 10. Test Prioritization Features **✅ NEW**

```bash
# Create a prioritization for an object
curl -X POST "http://localhost:8000/api/v1/projects/PROJECT_ID/prioritizations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "item_type": "object",
    "item_id": "OBJECT_ID",
    "priority_phase": "now",
    "score": 9,
    "notes": "High priority for MVP"
  }'

# Get prioritization board organized by phases
curl -X GET "http://localhost:8000/api/v1/projects/PROJECT_ID/prioritizations/board" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# Get prioritization statistics
curl -X GET "http://localhost:8000/api/v1/projects/PROJECT_ID/prioritizations/stats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# Bulk update prioritizations (drag-and-drop simulation)
curl -X POST "http://localhost:8000/api/v1/projects/PROJECT_ID/prioritizations/bulk-update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "updates": [
      {
        "item_id": "OBJECT_ID_1",
        "item_type": "object",
        "priority_phase": "now",
        "position": 1,
        "score": 9
      },
      {
        "item_id": "CTA_ID_1",
        "item_type": "cta",
        "priority_phase": "next",
        "position": 1,
        "score": 7
      }
    ]
  }'
```

### 11. Next Steps

Once you have the API working, you can:
1. Create more projects with full OOUX methodology support
2. Invite team members with role-based permissions
3. Track OOUX methodology progress across all 6 completed epics
4. **Prioritize all artifacts** using Now/Next/Later methodology **✅ NEW**
5. **Generate prioritization analytics** and board views **✅ NEW**
6. View the interactive dashboard UI
7. Test the real-time features (when Epic 7 is implemented)

The dashboard provides a complete foundation for the OOUX methodology workflow with production-ready prioritization features!
