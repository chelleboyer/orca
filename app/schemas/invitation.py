"""
Pydantic schemas for invitation and team management
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator

from app.models import ProjectInvitation, ProjectMember


class InvitationCreate(BaseModel):
    """Schema for creating a new invitation"""
    email: EmailStr = Field(..., description="Email address to invite")
    role: str = Field(..., description="Role to assign to the invited user")
    message: Optional[str] = Field(None, max_length=500, description="Optional custom message")
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['facilitator', 'contributor', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {valid_roles}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "colleague@example.com",
                "role": "contributor",
                "message": "Join our OOUX project!"
            }
        }


class InvitationResponse(BaseModel):
    """Schema for invitation response"""
    invitation_id: str = Field(..., description="Unique invitation ID")
    email: EmailStr = Field(..., description="Invited email address")
    role: str = Field(..., description="Assigned role")
    status: str = Field(..., description="Invitation status")
    message: Optional[str] = Field(None, description="Custom invitation message")
    sent_at: datetime = Field(..., description="When invitation was sent")
    expires_at: datetime = Field(..., description="When invitation expires")
    invited_by: Optional[Dict[str, Any]] = Field(None, description="Information about who sent the invitation")
    days_until_expiry: int = Field(..., description="Days until invitation expires")
    can_be_accepted: bool = Field(..., description="Whether invitation can still be accepted")
    
    @classmethod
    def from_invitation(cls, invitation: ProjectInvitation) -> "InvitationResponse":
        """Create response from ProjectInvitation object"""
        return cls(
            invitation_id=str(invitation.id),
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            message=invitation.message,
            sent_at=invitation.sent_at,
            expires_at=invitation.expires_at,
            invited_by={
                "id": str(invitation.inviter.id),
                "name": invitation.inviter.name,
                "email": invitation.inviter.email
            } if invitation.inviter else None,
            days_until_expiry=invitation.days_until_expiry,
            can_be_accepted=invitation.can_be_accepted
        )
    
    class Config:
        schema_extra = {
            "example": {
                "invitation_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "colleague@example.com",
                "role": "contributor",
                "status": "pending",
                "message": "Join our OOUX project!",
                "sent_at": "2025-08-31T10:00:00Z",
                "expires_at": "2025-09-07T10:00:00Z",
                "invited_by": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "days_until_expiry": 7,
                "can_be_accepted": True
            }
        }


class InvitationListResponse(BaseModel):
    """Schema for list of invitations"""
    invitations: List[Dict[str, Any]] = Field(..., description="List of invitations")
    
    class Config:
        schema_extra = {
            "example": {
                "invitations": [
                    {
                        "invitation_id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "colleague@example.com",
                        "role": "contributor",
                        "status": "pending",
                        "sent_at": "2025-08-31T10:00:00Z",
                        "expires_at": "2025-09-07T10:00:00Z",
                        "days_until_expiry": 7
                    }
                ]
            }
        }


class InvitationAcceptResponse(BaseModel):
    """Schema for invitation acceptance response"""
    success: bool = Field(..., description="Whether invitation was accepted successfully")
    message: str = Field(..., description="Success message")
    project_id: str = Field(..., description="ID of the project joined")
    project_title: str = Field(..., description="Title of the project joined")
    role: str = Field(..., description="Role assigned in the project")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Invitation accepted successfully",
                "project_id": "123e4567-e89b-12d3-a456-426614174002",
                "project_title": "My OOUX Project",
                "role": "contributor"
            }
        }


class ProjectMemberResponse(BaseModel):
    """Schema for project member response"""
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: EmailStr = Field(..., description="User email")
    role: str = Field(..., description="Member role in project")
    status: str = Field(..., description="Membership status")
    joined_at: Optional[datetime] = Field(None, description="When user joined project")
    invited_by: Optional[Dict[str, Any]] = Field(None, description="Who invited this user")
    permissions: List[str] = Field(..., description="List of permissions for this role")
    
    @classmethod
    def from_member(cls, member: ProjectMember) -> "ProjectMemberResponse":
        """Create response from ProjectMember object"""
        from app.core.permissions import ProjectPermissions
        
        return cls(
            user_id=str(member.user_id),
            name=member.user.name if member.user else "Unknown",
            email=member.user.email if member.user else "unknown@example.com",
            role=member.role,
            status=member.status,
            joined_at=member.joined_at,
            invited_by={
                "id": str(member.inviter.id),
                "name": member.inviter.name,
                "email": member.inviter.email
            } if member.inviter else None,
            permissions=ProjectPermissions.get_permissions_for_role(member.role)
        )
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174003",
                "name": "John Doe",
                "email": "john@example.com",
                "role": "facilitator",
                "status": "active",
                "joined_at": "2025-08-31T10:00:00Z",
                "invited_by": None,
                "permissions": [
                    "view_project",
                    "edit_objects",
                    "manage_members",
                    "invite_users"
                ]
            }
        }


class ProjectMembersResponse(BaseModel):
    """Schema for project members list response"""
    members: List[ProjectMemberResponse] = Field(..., description="List of active project members")
    pending_invitations: List[Dict[str, Any]] = Field(default=[], description="List of pending invitations")
    
    class Config:
        schema_extra = {
            "example": {
                "members": [
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174003",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "role": "facilitator",
                        "status": "active",
                        "joined_at": "2025-08-31T10:00:00Z",
                        "permissions": ["view_project", "edit_objects", "manage_members"]
                    }
                ],
                "pending_invitations": [
                    {
                        "invitation_id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "colleague@example.com",
                        "role": "contributor",
                        "status": "pending",
                        "expires_at": "2025-09-07T10:00:00Z"
                    }
                ]
            }
        }


class RoleChangeRequest(BaseModel):
    """Schema for changing a member's role"""
    role: str = Field(..., description="New role to assign")
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['facilitator', 'contributor', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {valid_roles}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "role": "contributor"
            }
        }


class InvitationPublicResponse(BaseModel):
    """Schema for public invitation information (no sensitive data)"""
    invitation_id: str = Field(..., description="Invitation ID")
    project_title: str = Field(..., description="Project title")
    project_description: Optional[str] = Field(None, description="Project description")
    role: str = Field(..., description="Role being offered")
    invited_by_name: str = Field(..., description="Name of person who sent invitation")
    expires_at: datetime = Field(..., description="When invitation expires")
    days_until_expiry: int = Field(..., description="Days until expiration")
    can_be_accepted: bool = Field(..., description="Whether invitation can be accepted")
    message: Optional[str] = Field(None, description="Custom invitation message")
    
    class Config:
        schema_extra = {
            "example": {
                "invitation_id": "123e4567-e89b-12d3-a456-426614174000",
                "project_title": "My OOUX Project",
                "project_description": "A collaborative UX design project",
                "role": "contributor",
                "invited_by_name": "John Doe",
                "expires_at": "2025-09-07T10:00:00Z",
                "days_until_expiry": 7,
                "can_be_accepted": True,
                "message": "Join our OOUX project!"
            }
        }
