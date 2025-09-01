"""
Project management API endpoints
"""

import uuid
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_from_token
from app.core.permissions import (
    require_project_access,
    require_project_facilitator,
    get_project_or_404,
    get_project_by_slug_or_404
)
from app.models import User, Project, ProjectMember
from app.services.project_service import ProjectService
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectSummary,
    ProjectDetail,
    ProjectListRequest,
    ProjectListResponse,
    ProjectStatusResponse,
    ProjectError,
    ProjectNotFoundError,
    ProjectPermissionError
)
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/projects", tags=["projects"])


# Dependency to get current user as User object
async def get_current_user(
    current_user_data: Annotated[dict, Depends(get_current_user_from_token)],
    db: Session = Depends(get_db)
) -> User:
    """Get current user as User object from token"""
    user_id = uuid.UUID(current_user_data["user_id"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


# Helper dependency functions
async def get_project_with_access(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[Project, ProjectMember]:
    """Get project and verify user has access"""
    from app.core.permissions import get_project_or_404, check_project_access
    project = get_project_or_404(project_id, db)
    membership = check_project_access(current_user, project, db)
    return project, membership


async def get_project_with_facilitator_access(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[Project, ProjectMember]:
    """Get project and verify user has facilitator access"""
    from app.core.permissions import get_project_or_404, check_project_access
    project = get_project_or_404(project_id, db)
    membership = check_project_access(current_user, project, db, required_role="facilitator")
    return project, membership


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new OOUX project. The creator automatically becomes a facilitator."
)
async def create_project(
    project_data: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new OOUX project.
    
    - **title**: Project title (3-100 characters)
    - **description**: Optional project description (max 1000 characters)
    
    The project creator is automatically assigned the facilitator role.
    """
    try:
        service = ProjectService(db)
        project, membership = service.create_project(project_data, current_user)
        
        return service.get_project_response(project, current_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List user's projects",
    description="Get a paginated list of projects the user has access to."
)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str = Query(None, max_length=100, description="Search term"),
    project_status: str = Query(None, description="Filter by project status"),
    my_role: str = Query(None, description="Filter by user's role"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of projects the user has access to.
    
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **search**: Search in project titles and descriptions
    - **project_status**: Filter by project status (active, archived)
    - **my_role**: Filter by user's role (facilitator, contributor, viewer)
    """
    try:
        # Convert string parameters to enums if provided
        status_enum = None
        if project_status:
            try:
                from app.schemas.project import ProjectStatus
                status_enum = ProjectStatus(project_status)
            except ValueError:
                status_enum = None
        
        role_enum = None
        if my_role:
            try:
                from app.schemas.project import ProjectMemberRole
                role_enum = ProjectMemberRole(my_role)
            except ValueError:
                role_enum = None
        
        request_params = ProjectListRequest(
            page=page,
            per_page=per_page,
            search=search,
            status=status_enum,
            my_role=role_enum
        )
        
        service = ProjectService(db)
        return service.get_user_projects(current_user, request_params)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.get(
    "/{project_id}",
    response_model=ProjectDetail,
    summary="Get project details",
    description="Get detailed information about a specific project."
)
async def get_project(
    project_access: Annotated[tuple[Project, ProjectMember], Depends(get_project_with_access)],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific project.
    
    Returns comprehensive project information including:
    - Project metadata and settings
    - List of project members and their roles
    - Project progress and statistics
    - User's role and permissions in the project
    """
    try:
        project, membership = project_access
        
        service = ProjectService(db)
        return service.get_project_detail(project, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project details: {str(e)}"
        )


@router.get(
    "/slug/{project_slug}",
    response_model=ProjectDetail,
    summary="Get project by slug",
    description="Get detailed information about a project using its URL slug."
)
async def get_project_by_slug(
    project_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a project using its URL slug.
    
    This endpoint allows accessing projects via human-readable URLs.
    """
    try:
        project = get_project_by_slug_or_404(project_slug, db)
        
        # Check access
        from app.core.permissions import check_project_access
        membership = check_project_access(current_user, project, db)
        
        service = ProjectService(db)
        return service.get_project_detail(project, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project details: {str(e)}"
        )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update project title and/or description. Requires facilitator role."
)
async def update_project(
    project_data: ProjectUpdateRequest,
    project_access: Annotated[tuple[Project, ProjectMember], Depends(get_project_with_facilitator_access)],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update project metadata (title and description).
    
    - **title**: New project title (optional, 3-100 characters)
    - **description**: New project description (optional, max 1000 characters)
    
    Only project facilitators can update project metadata.
    When the title is changed, the project slug is automatically updated.
    """
    try:
        project, membership = project_access
        
        service = ProjectService(db)
        updated_project = service.update_project(project, project_data, current_user)
        
        return service.get_project_response(updated_project, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.get(
    "/{project_id}/status",
    response_model=ProjectStatusResponse,
    summary="Get project status",
    description="Get project health status and statistics."
)
async def get_project_status(
    project_access: Annotated[tuple[Project, ProjectMember], Depends(get_project_with_access)],
    db: Session = Depends(get_db)
):
    """
    Get project status, health metrics, and statistics.
    
    Returns:
    - Project status (active, archived, deleted)
    - Health indicator (healthy, warning, critical)
    - Project statistics (completion, members, activity)
    - Recent activity summary
    """
    try:
        project, membership = project_access
        
        service = ProjectService(db)
        return service.get_project_status(project)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project status: {str(e)}"
        )


@router.post(
    "/{project_id}/archive",
    response_model=MessageResponse,
    summary="Archive project",
    description="Archive a project. Requires facilitator role."
)
async def archive_project(
    project_access: Annotated[tuple[Project, ProjectMember], Depends(get_project_with_facilitator_access)],
    db: Session = Depends(get_db)
):
    """
    Archive a project.
    
    Archived projects are hidden from active project lists but remain accessible.
    Only project facilitators can archive projects.
    """
    try:
        project, membership = project_access
        
        if project.status == "archived":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is already archived"
            )
        
        service = ProjectService(db)
        service.archive_project(project)
        
        return MessageResponse(message="Project archived successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive project: {str(e)}"
        )


@router.post(
    "/{project_id}/activate",
    response_model=MessageResponse,
    summary="Activate project",
    description="Activate an archived project. Requires facilitator role."
)
async def activate_project(
    project_access: Annotated[tuple[Project, ProjectMember], Depends(get_project_with_facilitator_access)],
    db: Session = Depends(get_db)
):
    """
    Activate an archived project.
    
    This restores an archived project to active status.
    Only project facilitators can activate projects.
    """
    try:
        project, membership = project_access
        
        if project.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is already active"
            )
        
        service = ProjectService(db)
        service.activate_project(project)
        
        return MessageResponse(message="Project activated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate project: {str(e)}"
        )


@router.delete(
    "/{project_id}",
    response_model=MessageResponse,
    summary="Delete project",
    description="Soft delete a project. Requires facilitator role."
)
async def delete_project(
    project_access: Annotated[tuple[Project, ProjectMember], Depends(get_project_with_facilitator_access)],
    db: Session = Depends(get_db)
):
    """
    Soft delete a project.
    
    This marks the project as deleted and deactivates all memberships.
    The project data is not physically removed from the database.
    Only project facilitators can delete projects.
    """
    try:
        project, membership = project_access
        
        if project.status == "deleted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is already deleted"
            )
        
        service = ProjectService(db)
        service.delete_project(project)
        
        return MessageResponse(message="Project deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )


@router.get(
    "/search",
    response_model=List[ProjectSummary],
    summary="Search projects",
    description="Search projects by title or description."
)
async def search_projects(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search projects by title or description.
    
    - **q**: Search query (required)
    - **limit**: Maximum number of results (default: 10, max: 50)
    
    Returns projects that match the search term in title or description.
    """
    try:
        service = ProjectService(db)
        return service.search_projects(current_user, q, limit)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search projects: {str(e)}"
        )
