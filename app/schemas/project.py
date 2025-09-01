"""
Project schemas for request/response validation and serialization
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectMemberRole(str, Enum):
    """Project member role enumeration"""
    FACILITATOR = "facilitator"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


class ProjectMemberStatus(str, Enum):
    """Project member status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"


# Base schemas for common patterns
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""
    created_at: datetime
    updated_at: datetime


class ProjectBase(BaseModel):
    """Base project schema with common fields"""
    title: str = Field(..., min_length=3, max_length=100, description="Project title")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty or only whitespace')
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


# Request schemas
class ProjectCreateRequest(ProjectBase):
    """Schema for project creation requests"""
    pass


class ProjectUpdateRequest(BaseModel):
    """Schema for project update requests"""
    title: Optional[str] = Field(None, min_length=3, max_length=100, description="Project title")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")

    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Title cannot be empty or only whitespace')
            return v.strip()
        return v

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


# Response schemas
class UserSummary(BaseModel):
    """User summary for project responses"""
    id: uuid.UUID
    name: str
    email: str

    class Config:
        from_attributes = True


class ProjectMemberResponse(TimestampMixin):
    """Project member response schema"""
    id: uuid.UUID
    user: UserSummary
    role: ProjectMemberRole
    status: ProjectMemberStatus
    invited_at: datetime
    joined_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectProgress(BaseModel):
    """Project progress and statistics"""
    objects: int = 0
    relationships: int = 0
    cta_matrix: int = 0
    overall_completion: float = 0.0


class ProjectSummary(TimestampMixin):
    """Project summary for listing"""
    id: uuid.UUID
    title: str
    description: Optional[str]
    slug: str
    status: ProjectStatus
    last_activity: datetime
    member_count: int
    my_role: ProjectMemberRole
    progress: ProjectProgress

    class Config:
        from_attributes = True


class ProjectDetail(TimestampMixin):
    """Detailed project information"""
    id: uuid.UUID
    title: str
    description: Optional[str]
    slug: str
    status: ProjectStatus
    last_activity: datetime
    created_by: UserSummary
    my_role: ProjectMemberRole
    members: List[ProjectMemberResponse] = []
    progress: ProjectProgress

    class Config:
        from_attributes = True


class ProjectResponse(TimestampMixin):
    """Project creation/update response"""
    id: uuid.UUID
    title: str
    description: Optional[str]
    slug: str
    status: ProjectStatus
    last_activity: datetime
    created_by: UserSummary
    member_count: int
    my_role: ProjectMemberRole

    class Config:
        from_attributes = True


# Pagination schemas
class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")


class ProjectListRequest(BaseModel):
    """Request schema for project listing with search and pagination"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, max_length=100, description="Search term")
    status: Optional[ProjectStatus] = Field(None, description="Filter by status")
    my_role: Optional[ProjectMemberRole] = Field(None, description="Filter by my role")

    @validator('search')
    def validate_search(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class ProjectListResponse(BaseModel):
    """Response schema for project listing"""
    projects: List[ProjectSummary]
    pagination: PaginationInfo


# Project status and health schemas
class ProjectStatistics(BaseModel):
    """Project statistics and metrics"""
    total_objects: int = 0
    total_relationships: int = 0
    total_cta_entries: int = 0
    completion_percentage: float = 0.0
    active_members: int = 0
    days_since_creation: int = 0


class ProjectActivity(BaseModel):
    """Recent project activity"""
    user: UserSummary
    action: str
    timestamp: datetime
    description: str


class ProjectStatusResponse(BaseModel):
    """Project status and health response"""
    project_id: uuid.UUID
    status: ProjectStatus
    health: str = "healthy"  # healthy, warning, critical
    last_activity: datetime
    statistics: ProjectStatistics
    recent_activity: List[ProjectActivity] = []


# Member management schemas
class ProjectMemberInviteRequest(BaseModel):
    """Schema for inviting users to projects"""
    email: str = Field(..., description="Email of user to invite")
    role: ProjectMemberRole = Field(..., description="Role to assign")

    @validator('email')
    def validate_email(cls, v):
        # Basic email validation
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v.lower()


class ProjectMemberUpdateRequest(BaseModel):
    """Schema for updating project member roles"""
    role: ProjectMemberRole = Field(..., description="New role to assign")


# Error response schemas
class ProjectError(BaseModel):
    """Project-specific error response"""
    error: str
    message: str
    details: Optional[dict] = None


class ProjectNotFoundError(ProjectError):
    """Project not found error"""
    error: str = "project_not_found"
    message: str = "Project not found or access denied"


class ProjectPermissionError(ProjectError):
    """Project permission error"""
    error: str = "insufficient_permissions"
    message: str = "Insufficient permissions for this action"


class ProjectValidationError(ProjectError):
    """Project validation error"""
    error: str = "validation_error"
    message: str = "Invalid input data"
