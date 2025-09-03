"""
API endpoints for project dashboard and navigation
"""

import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_project_access
from app.models import User
from app.services.dashboard_service import DashboardService
from app.services.cta_service import CTAService
from app.core.exceptions import NotFoundError, PermissionError
from app.schemas.dashboard import (
    ProjectDashboardResponse,
    ProjectNavigationResponse,
    UserProjectsResponse,
    ProjectSummary
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get(
    "/test-guide",
    response_class=HTMLResponse,
    summary="Development Test Guide",
    description="Interactive guide for testing CTA Matrix functionality"
)
async def test_guide(request: Request):
    """Serve the development test guide"""
    try:
        with open("app/static/test_guide.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Test Guide Not Found</h1><p>The test guide file is missing.</p>",
            status_code=404
        )


@router.get(
    "/projects/{project_id}/dashboard",
    response_model=ProjectDashboardResponse,
    summary="Get project dashboard",
    description="Get comprehensive dashboard data for a project including team, progress, and activity"
)
async def get_project_dashboard(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ProjectDashboardResponse:
    """Get project dashboard data"""
    dashboard_service = DashboardService(db)
    
    try:
        dashboard_data = dashboard_service.get_project_dashboard_data(
            project_id=project_id,
            user_id=current_user.id
        )
        
        return ProjectDashboardResponse(**dashboard_data)
        
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/projects/{project_id}/navigation",
    response_model=ProjectNavigationResponse,
    summary="Get project navigation",
    description="Get OOUX methodology navigation structure with progress indicators"
)
async def get_project_navigation(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ProjectNavigationResponse:
    """Get project navigation structure"""
    dashboard_service = DashboardService(db)
    
    try:
        navigation_data = dashboard_service.get_project_navigation_data(
            project_id=project_id,
            user_id=current_user.id
        )
        
        return ProjectNavigationResponse(**navigation_data)
        
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/user/projects",
    response_model=UserProjectsResponse,
    summary="Get user projects",
    description="Get list of projects the user has access to for navigation"
)
async def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProjectsResponse:
    """Get user's accessible projects"""
    dashboard_service = DashboardService(db)
    
    projects = dashboard_service.get_user_projects_list(current_user.id)
    
    # Convert dictionaries to ProjectSummary objects
    project_summaries = [
        ProjectSummary(**project) for project in projects
    ]
    
    return UserProjectsResponse(projects=project_summaries)


@router.post(
    "/projects/{project_id}/activity",
    response_model=Dict[str, Any],
    summary="Update project activity",
    description="Update project last activity timestamp when user performs actions"
)
async def update_project_activity(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update project activity timestamp"""
    # Verify user has access to project
    project, membership = require_project_access(project_id, current_user, db)
    
    dashboard_service = DashboardService(db)
    dashboard_service.update_project_activity(project_id, current_user.id)
    
    return {
        "success": True,
        "message": "Project activity updated",
        "timestamp": project.last_activity.isoformat() if project.last_activity else None
    }


@router.get(
    "/projects/{project_id}/stats",
    response_model=Dict[str, Any],
    summary="Get project statistics",
    description="Get project statistics and metrics for dashboard widgets"
)
async def get_project_statistics(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get project statistics"""
    # Verify user has access to project
    project, membership = require_project_access(project_id, current_user, db)
    
    dashboard_service = DashboardService(db)
    
    # Get basic project stats
    orca_progress = dashboard_service._get_orca_progress(project_id)
    project_stats = dashboard_service._get_project_statistics(project_id)
    
    # Calculate additional metrics
    overall_progress = dashboard_service._calculate_overall_progress(project_id)
    
    return {
        "project_id": str(project_id),
        "overall_progress": overall_progress,
        "orca_sections": orca_progress,
        "statistics": project_stats,
        "last_updated": project.last_activity.isoformat() if project.last_activity else None
    }


@router.get(
    "/projects/{project_id}/recent-activity",
    response_model=Dict[str, List[Dict[str, Any]]],
    summary="Get recent activity",
    description="Get recent project activity feed for dashboard"
)
async def get_recent_activity(
    project_id: uuid.UUID,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """Get recent project activity"""
    # Verify user has access to project
    project, membership = require_project_access(project_id, current_user, db)
    
    dashboard_service = DashboardService(db)
    activities = dashboard_service._get_recent_activity(project_id)
    
    # Limit results
    limited_activities = activities[:limit]
    
    return {
        "activities": limited_activities
    }


# HTML Routes for Frontend Dashboard Pages

@router.get(
    "/test-simple",
    response_class=HTMLResponse,
    summary="Simple Test Page",
    description="Simple test page to debug HTMX issues"
)
async def test_simple_page(request: Request):
    """Render simple test page"""
    return templates.TemplateResponse(
        "test_simple.html",
        {"request": request}
    )


@router.get(
    "/test-guide",
    response_class=HTMLResponse,
    summary="Development Test Guide",
    description="Interactive guide for testing CTA Matrix features"
)
async def test_guide_page(request: Request):
    """Render test guide page"""
    return templates.TemplateResponse(
        "test_guide.html",
        {"request": request}
    )


@router.get(
    "/demo/cta-matrix",
    response_class=HTMLResponse,
    summary="CTA Matrix Demo Page (No Auth)",
    description="Demo version of CTA Matrix interface for development testing"
)
async def cta_matrix_demo_page(
    request: Request
):
    """Render CTA Matrix demo page without authentication"""
    try:
        # Demo project ID
        demo_project_id = uuid.uuid4()
        
        # Demo data structure for testing
        mock_matrix_data = {
            "project_id": str(demo_project_id),
            "roles": [
                {"id": "role1", "name": "User", "description": "Standard user"},
                {"id": "role2", "name": "Admin", "description": "Administrator"},
                {"id": "role3", "name": "Manager", "description": "Project manager"},
            ],
            "objects": [
                {"id": "obj1", "name": "Account", "core_noun": "Account"},
                {"id": "obj2", "name": "Project", "core_noun": "Project"},
                {"id": "obj3", "name": "Report", "core_noun": "Report"},
            ],
            "rows": [
                {
                    "role_id": "role1",
                    "role_name": "User", 
                    "role_description": "Standard user",
                    "cells": [
                        {
                            "role_id": "role1",
                            "object_id": "obj1",
                            "has_create": True,
                            "has_read": True,
                            "has_update": False,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 2,
                            "primary_ctas": []
                        },
                        {
                            "role_id": "role1",
                            "object_id": "obj2",
                            "has_create": False,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 2,
                            "primary_ctas": []
                        },
                        {
                            "role_id": "role1",
                            "object_id": "obj3",
                            "has_create": False,
                            "has_read": True,
                            "has_update": False,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 1,
                            "primary_ctas": []
                        }
                    ]
                }
            ],
            "total_ctas": 5,
            "populated_cells": 3
        }
        
        # Mock project data
        mock_project = type('Project', (), {
            'id': demo_project_id,
            'title': 'OOUX ORCA Demo Project',
            'description': 'Demo project for CTA Matrix testing'
        })()
        
        # Mock user data
        mock_user = type('User', (), {
            'id': uuid.uuid4(),
            'name': 'Demo User',
            'email': 'demo@example.com'
        })()
        
        # Get user permissions
        permissions = ["view_content", "edit_ctas", "export_data"]
        
        return templates.TemplateResponse(
            "dashboard/cta_matrix_demo.html",
            {
                "request": request,
                "project": mock_project,
                "matrix_data": mock_matrix_data,
                "permissions": permissions,
                "current_user": mock_user,
                "current_user_role": "facilitator",
                "is_demo": True  # Flag to indicate this is demo mode
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/projects/{project_id}/cta-matrix",
    response_class=HTMLResponse,
    summary="CTA Matrix Page",
    description="Render the CTA Matrix interface page"
)
async def cta_matrix_page(
    request: Request,
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Render CTA Matrix page"""
    try:
        # For now, create mock data structure to get the frontend working
        # This will be replaced with actual service calls once the async issues are resolved
        
        mock_matrix_data = {
            "project_id": str(project_id),
            "roles": [
                {"id": "role1", "name": "User", "description": "Standard user"},
                {"id": "role2", "name": "Admin", "description": "Administrator"},
            ],
            "objects": [
                {"id": "obj1", "name": "Account", "core_noun": "Account"},
                {"id": "obj2", "name": "Project", "core_noun": "Project"},
            ],
            "rows": [
                {
                    "role_id": "role1",
                    "role_name": "User", 
                    "role_description": "Standard user",
                    "cells": [
                        {
                            "role_id": "role1",
                            "object_id": "obj1",
                            "has_create": True,
                            "has_read": True,
                            "has_update": False,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 2,
                            "primary_ctas": []
                        }
                    ]
                }
            ],
            "total_ctas": 2,
            "populated_cells": 1
        }
        
        # Mock project data
        mock_project = type('Project', (), {
            'id': project_id,
            'title': 'OOUX ORCA Project',
            'description': 'Test project for CTA Matrix'
        })()
        
        # Get user permissions
        permissions = ["view_content", "edit_ctas", "export_data"]
        
        return templates.TemplateResponse(
            "dashboard/cta_matrix.html",
            {
                "request": request,
                "project": mock_project,
                "matrix_data": mock_matrix_data,
                "permissions": permissions,
                "current_user": current_user,
                "current_user_role": "facilitator"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/demo/cta-matrix-grid",
    response_class=HTMLResponse,
    summary="CTA Matrix Grid Demo HTMX",
    description="Demo HTMX partial for CTA matrix grid"
)
async def cta_matrix_grid_demo_htmx(
    request: Request
):
    """Render CTA Matrix grid partial via HTMX - demo version"""
    try:
        demo_project_id = uuid.uuid4()
        
        # Enhanced mock matrix data for demo
        mock_matrix_data = {
            "project_id": str(demo_project_id),
            "roles": [
                {"id": "role1", "name": "User", "description": "Standard user"},
                {"id": "role2", "name": "Admin", "description": "Administrator"},
                {"id": "role3", "name": "Manager", "description": "Project manager"},
            ],
            "objects": [
                {"id": "obj1", "name": "Account", "core_noun": "Account"},
                {"id": "obj2", "name": "Project", "core_noun": "Project"},
                {"id": "obj3", "name": "Report", "core_noun": "Report"},
            ],
            "rows": [
                {
                    "role_id": "role1",
                    "role_name": "User", 
                    "role_description": "Standard user",
                    "cells": [
                        {
                            "role_id": "role1",
                            "object_id": "obj1",
                            "has_create": True,
                            "has_read": True,
                            "has_update": False,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 2,
                            "primary_ctas": [
                                {"verb": "create", "description": "Create account", "crud_type": "CREATE"},
                                {"verb": "view", "description": "View account", "crud_type": "READ"}
                            ]
                        },
                        {
                            "role_id": "role1",
                            "object_id": "obj2",
                            "has_create": False,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 2,
                            "primary_ctas": []
                        },
                        {
                            "role_id": "role1",
                            "object_id": "obj3",
                            "has_create": False,
                            "has_read": True,
                            "has_update": False,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 1,
                            "primary_ctas": []
                        }
                    ]
                },
                {
                    "role_id": "role2",
                    "role_name": "Admin", 
                    "role_description": "Administrator",
                    "cells": [
                        {
                            "role_id": "role2",
                            "object_id": "obj1",
                            "has_create": True,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": True,
                            "has_none": False,
                            "total_ctas": 4,
                            "primary_ctas": []
                        },
                        {
                            "role_id": "role2",
                            "object_id": "obj2",
                            "has_create": True,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": True,
                            "has_none": False,
                            "total_ctas": 4,
                            "primary_ctas": []
                        },
                        {
                            "role_id": "role2",
                            "object_id": "obj3",
                            "has_create": True,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": True,
                            "has_none": False,
                            "total_ctas": 4,
                            "primary_ctas": []
                        }
                    ]
                },
                {
                    "role_id": "role3",
                    "role_name": "Manager", 
                    "role_description": "Project manager",
                    "cells": [
                        {
                            "role_id": "role3",
                            "object_id": "obj1",
                            "has_create": False,
                            "has_read": True,
                            "has_update": False,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 1,
                            "primary_ctas": []
                        },
                        {
                            "role_id": "role3",
                            "object_id": "obj2",
                            "has_create": True,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 3,
                            "primary_ctas": []
                        },
                        {
                            "role_id": "role3",
                            "object_id": "obj3",
                            "has_create": True,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 3,
                            "primary_ctas": []
                        }
                    ]
                }
            ],
            "total_ctas": 24,
            "populated_cells": 9
        }
        
        permissions = ["view_content", "edit_ctas", "export_data"]
        
        return templates.TemplateResponse(
            "dashboard/cta_matrix_grid.html",
            {
                "request": request,
                "project_id": demo_project_id,
                "matrix_data": mock_matrix_data,
                "permissions": permissions,
                "is_demo": True  # Flag for demo mode
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/htmx/demo/cta-matrix-grid",
    response_class=HTMLResponse,
    summary="CTA Matrix Grid Demo HTMX Alias",
    description="Alias for demo HTMX partial to match template expectations"
)
async def cta_matrix_grid_demo_htmx_alias(
    request: Request
):
    """Alias for demo HTMX route"""
    return await cta_matrix_grid_demo_htmx(request)


@router.get(
    "/demo/cta-cell/{role_id}/{object_id}",
    response_class=HTMLResponse,
    summary="CTA Cell Edit Modal Demo HTMX",
    description="Demo HTMX partial for CTA cell editing modal"
)
async def cta_cell_modal_demo_htmx(
    request: Request,
    role_id: str,
    object_id: str
):
    """Render CTA cell edit modal partial via HTMX - demo version"""
    try:
        demo_project_id = uuid.uuid4()
        
        # Mock CTA data for role-object combination
        existing_ctas = [
            {
                "id": "cta1",
                "crud_type": "CREATE",
                "description": "Create new account",
                "business_value": "Enable new user registration",
                "priority": 5,
                "preconditions": "User must be authenticated",
                "postconditions": "Account is created and activated",
                "is_primary": True
            },
            {
                "id": "cta2", 
                "crud_type": "READ",
                "description": "View account details",
                "business_value": "Allow users to see their account info",
                "priority": 3,
                "preconditions": "User must own the account",
                "postconditions": None,
                "is_primary": False
            }
        ]
        
        # Mock role and object names based on IDs
        role_names = {"role1": "User", "role2": "Admin", "role3": "Manager"}
        object_names = {"obj1": "Account", "obj2": "Project", "obj3": "Report"}
        
        role_name = role_names.get(role_id, "Unknown Role")
        object_name = object_names.get(object_id, "Unknown Object")
        
        permissions = ["view_content", "edit_ctas"]
        
        return templates.TemplateResponse(
            "dashboard/cta_cell_modal.html",
            {
                "request": request,
                "project_id": demo_project_id,
                "role_id": role_id,
                "object_id": object_id,
                "role_name": role_name,
                "object_name": object_name,
                "existing_ctas": existing_ctas,
                "permissions": permissions
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/htmx/demo/cta-cell/{role_id}/{object_id}",
    response_class=HTMLResponse,
    summary="CTA Cell Edit Modal Demo HTMX Alias",
    description="Alias for demo modal HTMX partial"
)
async def cta_cell_modal_demo_htmx_alias(
    request: Request,
    role_id: str,
    object_id: str
):
    """Alias for demo CTA cell modal route"""
    return await cta_cell_modal_demo_htmx(request, role_id, object_id)


@router.get(
    "/htmx/projects/{project_id}/cta-matrix-grid",
    response_class=HTMLResponse,
    summary="CTA Matrix Grid HTMX",
    description="HTMX partial for CTA matrix grid"
)
async def cta_matrix_grid_htmx(
    request: Request,
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Render CTA Matrix grid partial via HTMX"""
    try:
        # Mock matrix data for initial implementation
        mock_matrix_data = {
            "project_id": str(project_id),
            "roles": [
                {"id": "role1", "name": "User", "description": "Standard user"},
                {"id": "role2", "name": "Admin", "description": "Administrator"},
            ],
            "objects": [
                {"id": "obj1", "name": "Account", "core_noun": "Account"},
                {"id": "obj2", "name": "Project", "core_noun": "Project"},
            ],
            "rows": [
                {
                    "role_id": "role1",
                    "role_name": "User", 
                    "role_description": "Standard user",
                    "cells": [
                        {
                            "role_id": "role1",
                            "object_id": "obj1",
                            "has_create": True,
                            "has_read": True,
                            "has_update": False,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 2,
                            "primary_ctas": [
                                {"verb": "create", "description": "Create account", "crud_type": "CREATE"},
                                {"verb": "view", "description": "View account", "crud_type": "READ"}
                            ]
                        },
                        {
                            "role_id": "role1",
                            "object_id": "obj2",
                            "has_create": False,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": False,
                            "has_none": False,
                            "total_ctas": 2,
                            "primary_ctas": []
                        }
                    ]
                },
                {
                    "role_id": "role2",
                    "role_name": "Admin", 
                    "role_description": "Administrator",
                    "cells": [
                        {
                            "role_id": "role2",
                            "object_id": "obj1",
                            "has_create": True,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": True,
                            "has_none": False,
                            "total_ctas": 4,
                            "primary_ctas": []
                        },
                        {
                            "role_id": "role2",
                            "object_id": "obj2",
                            "has_create": True,
                            "has_read": True,
                            "has_update": True,
                            "has_delete": True,
                            "has_none": False,
                            "total_ctas": 4,
                            "primary_ctas": []
                        }
                    ]
                }
            ],
            "total_ctas": 12,
            "populated_cells": 4
        }
        
        permissions = ["view_content", "edit_ctas", "export_data"]
        
        return templates.TemplateResponse(
            "dashboard/cta_matrix_grid.html",
            {
                "request": request,
                "project_id": project_id,
                "matrix_data": mock_matrix_data,
                "permissions": permissions
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/htmx/projects/{project_id}/cta-cell/{role_id}/{object_id}",
    response_class=HTMLResponse,
    summary="CTA Cell Edit Modal HTMX",
    description="HTMX partial for CTA cell editing modal"
)
async def cta_cell_modal_htmx(
    request: Request,
    project_id: uuid.UUID,
    role_id: str,
    object_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Render CTA cell edit modal partial via HTMX"""
    try:
        # Mock CTA data for role-object combination
        existing_ctas = [
            {
                "id": "cta1",
                "crud_type": "CREATE",
                "description": "Create new account",
                "business_value": "Enable new user registration",
                "priority": 5,
                "preconditions": "User must be authenticated",
                "postconditions": "Account is created and activated",
                "is_primary": True
            },
            {
                "id": "cta2", 
                "crud_type": "READ",
                "description": "View account details",
                "business_value": "Allow users to see their account info",
                "priority": 3,
                "preconditions": "User must own the account",
                "postconditions": None,
                "is_primary": False
            }
        ]
        
        # Mock role and object names
        role_name = "User" if role_id == "role1" else "Admin"
        object_name = "Account" if object_id == "obj1" else "Project"
        
        permissions = ["view_content", "edit_ctas"]
        
        return templates.TemplateResponse(
            "dashboard/cta_cell_modal.html",
            {
                "request": request,
                "project_id": project_id,
                "role_id": role_id,
                "object_id": object_id,
                "role_name": role_name,
                "object_name": object_name,
                "existing_ctas": existing_ctas,
                "permissions": permissions
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
