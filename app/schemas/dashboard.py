"""
Pydantic schemas for dashboard and navigation
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProjectMetadata(BaseModel):
    """Project metadata for dashboard"""
    id: str = Field(..., description="Project ID")
    title: str = Field(..., description="Project title")
    description: Optional[str] = Field(None, description="Project description")
    slug: str = Field(..., description="Project slug")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    status: str = Field(..., description="Project status")
    owner: Optional[Dict[str, Any]] = Field(None, description="Project owner information")


class TeamMember(BaseModel):
    """Team member information for dashboard"""
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="Member role")
    joined_at: Optional[str] = Field(None, description="Join timestamp")
    invited_by: Optional[Dict[str, str]] = Field(None, description="Inviter information")
    last_active: Optional[str] = Field(None, description="Last activity timestamp")
    avatar_url: str = Field(..., description="Avatar URL")
    permissions: List[str] = Field(..., description="User permissions")


class OrcaSection(BaseModel):
    """OOUX methodology section progress"""
    status: str = Field(..., description="Section status (not_started, in_progress, complete)")
    progress_percentage: int = Field(..., description="Progress percentage")
    artifact_count: int = Field(..., description="Number of artifacts in section")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")


class RecentActivity(BaseModel):
    """Recent activity item"""
    id: str = Field(..., description="Activity ID")
    type: str = Field(..., description="Activity type")
    user: str = Field(..., description="User who performed action")
    description: str = Field(..., description="Activity description")
    timestamp: str = Field(..., description="Activity timestamp")
    artifact_id: Optional[str] = Field(None, description="Related artifact ID")


class ProjectStatistics(BaseModel):
    """Project statistics"""
    total_objects: int = Field(..., description="Total number of objects")
    total_relationships: int = Field(..., description="Total number of relationships")
    total_ctas: int = Field(..., description="Total number of CTAs")
    total_attributes: int = Field(..., description="Total number of attributes")
    team_size: int = Field(..., description="Number of team members")
    pending_invitations: int = Field(..., description="Number of pending invitations")


class ProjectDashboardResponse(BaseModel):
    """Complete project dashboard response"""
    project: ProjectMetadata = Field(..., description="Project metadata")
    current_user_role: str = Field(..., description="Current user's role")
    permissions: List[str] = Field(..., description="Current user's permissions")
    team_members: List[TeamMember] = Field(..., description="Team members")
    orca_progress: Dict[str, OrcaSection] = Field(..., description="OOUX methodology progress")
    recent_activity: List[RecentActivity] = Field(..., description="Recent activity feed")
    project_statistics: ProjectStatistics = Field(..., description="Project statistics")
    pending_invitations: List[Dict[str, Any]] = Field(..., description="Pending invitations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "My OOUX Project",
                    "description": "A collaborative UX design project",
                    "slug": "my-ooux-project",
                    "created_at": "2025-08-31T10:00:00Z",
                    "updated_at": "2025-08-31T15:30:00Z",
                    "last_activity": "2025-08-31T15:30:00Z",
                    "status": "active",
                    "owner": {
                        "id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "John Doe",
                        "email": "john@example.com"
                    }
                },
                "current_user_role": "facilitator",
                "permissions": ["view_project", "edit_objects", "manage_members"],
                "team_members": [
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "role": "facilitator",
                        "joined_at": "2025-08-31T10:00:00Z",
                        "invited_by": None,
                        "last_active": "2025-08-31T15:00:00Z",
                        "avatar_url": "/api/v1/users/123e4567-e89b-12d3-a456-426614174001/avatar",
                        "permissions": ["view_project", "edit_objects"]
                    }
                ],
                "orca_progress": {
                    "object_catalog": {
                        "status": "complete",
                        "progress_percentage": 100,
                        "artifact_count": 15,
                        "last_updated": "2025-08-30T16:00:00Z"
                    },
                    "nom_matrix": {
                        "status": "in_progress",
                        "progress_percentage": 65,
                        "artifact_count": 23,
                        "last_updated": "2025-08-31T10:30:00Z"
                    }
                },
                "recent_activity": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174002",
                        "type": "object_created",
                        "user": "John Doe",
                        "description": "Created object 'User Profile'",
                        "timestamp": "2025-08-31T14:30:00Z",
                        "artifact_id": "123e4567-e89b-12d3-a456-426614174003"
                    }
                ],
                "project_statistics": {
                    "total_objects": 15,
                    "total_relationships": 23,
                    "total_ctas": 8,
                    "total_attributes": 42,
                    "team_size": 5,
                    "pending_invitations": 2
                },
                "pending_invitations": []
            }
        }


class NavigationSection(BaseModel):
    """Navigation section for OOUX methodology"""
    id: str = Field(..., description="Section ID")
    name: str = Field(..., description="Section name")
    description: str = Field(..., description="Section description")
    route: str = Field(..., description="Frontend route")
    icon: str = Field(..., description="Icon identifier")
    required_permission: str = Field(..., description="Required permission")
    can_edit: bool = Field(..., description="Whether user can edit in this section")
    status: str = Field(..., description="Section status")
    progress_percentage: int = Field(..., description="Progress percentage")
    artifact_count: int = Field(..., description="Number of artifacts")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")


class ProjectNavigationResponse(BaseModel):
    """Project navigation structure response"""
    sections: List[NavigationSection] = Field(..., description="Navigation sections")
    user_role: str = Field(..., description="User's role in project")
    overall_progress: int = Field(..., description="Overall project progress percentage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sections": [
                    {
                        "id": "object_catalog",
                        "name": "Object Catalog",
                        "description": "Define and categorize your system objects",
                        "route": "/projects/123e4567-e89b-12d3-a456-426614174000/objects",
                        "icon": "cube",
                        "required_permission": "view_content",
                        "can_edit": True,
                        "status": "complete",
                        "progress_percentage": 100,
                        "artifact_count": 15,
                        "last_updated": "2025-08-30T16:00:00Z"
                    }
                ],
                "user_role": "facilitator",
                "overall_progress": 65
            }
        }


class ProjectSummary(BaseModel):
    """Project summary for user projects list"""
    id: str = Field(..., description="Project ID")
    title: str = Field(..., description="Project title")
    slug: str = Field(..., description="Project slug")
    description: Optional[str] = Field(None, description="Project description")
    role: str = Field(..., description="User's role in project")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    member_count: int = Field(..., description="Number of team members")
    progress_percentage: int = Field(..., description="Overall progress percentage")


class UserProjectsResponse(BaseModel):
    """User projects list response"""
    projects: List[ProjectSummary] = Field(..., description="List of user's projects")
    
    class Config:
        json_schema_extra = {
            "example": {
                "projects": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "My OOUX Project",
                        "slug": "my-ooux-project",
                        "description": "A collaborative UX design project",
                        "role": "facilitator",
                        "last_activity": "2025-08-31T15:30:00Z",
                        "member_count": 5,
                        "progress_percentage": 65
                    }
                ]
            }
        }
