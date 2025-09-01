"""
Role-based permission system for project management
"""

import uuid
from functools import wraps
from typing import Optional, List, Union, Annotated

from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_from_token
from app.models import User, Project, ProjectMember
from app.schemas.project import ProjectMemberRole


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


class ProjectPermissions:
    """Project permission definitions and checking utilities"""
    
    # Role hierarchy (higher number = more permissions)
    ROLE_HIERARCHY = {
        "viewer": 1,
        "contributor": 2, 
        "facilitator": 3
    }
    
    # Permission mappings
    PERMISSIONS = {
        "view_project": ["viewer", "contributor", "facilitator"],
        "view_project_details": ["viewer", "contributor", "facilitator"],
        "create_objects": ["contributor", "facilitator"],
        "edit_objects": ["contributor", "facilitator"],
        "delete_objects": ["facilitator"],
        "edit_project": ["facilitator"],
        "manage_members": ["facilitator"],
        "archive_project": ["facilitator"],
        "delete_project": ["facilitator"],
    }

    @classmethod
    def has_permission(cls, user_role: str, permission: str) -> bool:
        """
        Check if a role has a specific permission
        
        Args:
            user_role: The user's role in the project
            permission: The permission to check
            
        Returns:
            True if role has permission, False otherwise
        """
        return user_role in cls.PERMISSIONS.get(permission, [])

    @classmethod
    def can_perform_action(cls, user_role: str, required_role: str) -> bool:
        """
        Check if user role can perform action requiring a specific role
        
        Args:
            user_role: The user's current role
            required_role: The minimum role required
            
        Returns:
            True if user can perform action, False otherwise
        """
        user_level = cls.ROLE_HIERARCHY.get(user_role, 0)
        required_level = cls.ROLE_HIERARCHY.get(required_role, 999)
        return user_level >= required_level

    @classmethod
    def get_accessible_roles(cls, user_role: str) -> List[str]:
        """
        Get list of roles that user can assign to others
        
        Args:
            user_role: The user's current role
            
        Returns:
            List of roles user can assign
        """
        if user_role == "facilitator":
            return ["viewer", "contributor", "facilitator"]
        return []


def get_project_or_404(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> Project:
    """
    Get project by ID or raise 404 if not found
    
    Args:
        project_id: The project ID
        db: Database session
        
    Returns:
        Project object
        
    Raises:
        HTTPException: 404 if project not found
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.status != "deleted"
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


def get_project_by_slug_or_404(
    project_slug: str,
    db: Session = Depends(get_db)
) -> Project:
    """
    Get project by slug or raise 404 if not found
    
    Args:
        project_slug: The project slug
        db: Database session
        
    Returns:
        Project object
        
    Raises:
        HTTPException: 404 if project not found
    """
    project = db.query(Project).filter(
        Project.slug == project_slug,
        Project.status != "deleted"
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


def get_user_project_membership(
    user: User,
    project: Project,
    db: Session
) -> Optional[ProjectMember]:
    """
    Get user's membership in a project
    
    Args:
        user: The user
        project: The project
        db: Database session
        
    Returns:
        ProjectMember object if user is member, None otherwise
    """
    return db.query(ProjectMember).filter(
        ProjectMember.user_id == user.id,
        ProjectMember.project_id == project.id,
        ProjectMember.status == "active"
    ).first()


def check_project_access(
    user: User,
    project: Project,
    db: Session,
    required_permission: Optional[str] = None,
    required_role: Optional[str] = None
) -> ProjectMember:
    """
    Check if user has access to project and required permissions
    
    Args:
        user: The user
        project: The project  
        db: Database session
        required_permission: Specific permission needed
        required_role: Minimum role required
        
    Returns:
        ProjectMember object if access granted
        
    Raises:
        HTTPException: 403 if access denied
    """
    # Check if user is member of project
    membership = get_user_project_membership(user, project, db)
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Not a member of this project"
        )
    
    # Check specific permission
    if required_permission:
        if not ProjectPermissions.has_permission(membership.role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Insufficient permissions for {required_permission}"
            )
    
    # Check minimum role
    if required_role:
        if not ProjectPermissions.can_perform_action(membership.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {required_role} role or higher required"
            )
    
    return membership


def require_project_permission(
    permission: str,
    by_slug: bool = False
):
    """
    Decorator to require specific project permission
    
    Args:
        permission: The permission required
        by_slug: Whether to get project by slug instead of ID
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from function parameters
            db = None
            current_user = None
            project_id_or_slug = None
            
            # Find dependencies in kwargs (for dependency injection)
            for key, value in kwargs.items():
                if isinstance(value, Session):
                    db = value
                elif isinstance(value, User):
                    current_user = value
                elif key in ['project_id', 'project_slug']:
                    project_id_or_slug = value
            
            if not all([db, current_user, project_id_or_slug]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies for permission check"
                )
            
            # Get project
            if by_slug:
                project = get_project_by_slug_or_404(project_id_or_slug, db)
            else:
                project = get_project_or_404(project_id_or_slug, db)
            
            # Check access
            membership = check_project_access(
                current_user, 
                project, 
                db, 
                required_permission=permission
            )
            
            # Add project and membership to kwargs
            kwargs['project'] = project
            kwargs['membership'] = membership
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_project_role(
    role: str,
    by_slug: bool = False
):
    """
    Decorator to require minimum project role
    
    Args:
        role: The minimum role required
        by_slug: Whether to get project by slug instead of ID
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from function parameters
            db = None
            current_user = None
            project_id_or_slug = None
            
            # Find dependencies in kwargs
            for key, value in kwargs.items():
                if isinstance(value, Session):
                    db = value
                elif isinstance(value, User):
                    current_user = value
                elif key in ['project_id', 'project_slug']:
                    project_id_or_slug = value
            
            if not all([db, current_user, project_id_or_slug]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies for permission check"
                )
            
            # Get project
            if by_slug:
                project = get_project_by_slug_or_404(project_id_or_slug, db)
            else:
                project = get_project_or_404(project_id_or_slug, db)
            
            # Check access
            membership = check_project_access(
                current_user, 
                project, 
                db, 
                required_role=role
            )
            
            # Add project and membership to kwargs
            kwargs['project'] = project
            kwargs['membership'] = membership
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Dependency functions for FastAPI
def require_project_access(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[Project, ProjectMember]:
    """
    FastAPI dependency to check basic project access
    
    Args:
        project_id: The project ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Tuple of (Project, ProjectMember)
    """
    project = get_project_or_404(project_id, db)
    membership = check_project_access(current_user, project, db)
    return project, membership


def require_project_facilitator(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[Project, ProjectMember]:
    """
    FastAPI dependency to require facilitator role
    
    Args:
        project_id: The project ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Tuple of (Project, ProjectMember)
    """
    project = get_project_or_404(project_id, db)
    membership = check_project_access(
        current_user, 
        project, 
        db, 
        required_role="facilitator"
    )
    return project, membership


def require_project_contributor(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[Project, ProjectMember]:
    """
    FastAPI dependency to require contributor role or higher
    
    Args:
        project_id: The project ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Tuple of (Project, ProjectMember)
    """
    project = get_project_or_404(project_id, db)
    membership = check_project_access(
        current_user, 
        project, 
        db, 
        required_role="contributor"
    )
    return project, membership


# Helper functions for project creation and management
def create_project_facilitator_membership(
    project: Project,
    user: User,
    db: Session
) -> ProjectMember:
    """
    Create facilitator membership for project creator
    
    Args:
        project: The project
        user: The user (project creator)
        db: Database session
        
    Returns:
        ProjectMember object
    """
    from datetime import datetime
    
    membership = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role="facilitator",
        status="active",
        invited_by=user.id,
        joined_at=datetime.utcnow()
    )
    
    db.add(membership)
    return membership


def check_slug_exists(slug: str, db: Session, exclude_id: Optional[uuid.UUID] = None) -> bool:
    """
    Check if a project slug already exists
    
    Args:
        slug: The slug to check
        db: Database session
        exclude_id: Project ID to exclude from check (for updates)
        
    Returns:
        True if slug exists, False otherwise
    """
    query = db.query(Project).filter(
        Project.slug == slug,
        Project.status != "deleted"
    )
    
    if exclude_id:
        query = query.filter(Project.id != exclude_id)
    
    return query.first() is not None
