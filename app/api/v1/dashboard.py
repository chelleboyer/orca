"""
API endpoints for project dashboard and navigation
"""

import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_project_access
from app.models import User
from app.services.dashboard_service import DashboardService
from app.core.exceptions import NotFoundError, PermissionError
from app.schemas.dashboard import (
    ProjectDashboardResponse,
    ProjectNavigationResponse,
    UserProjectsResponse,
    ProjectSummary
)

router = APIRouter()


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
