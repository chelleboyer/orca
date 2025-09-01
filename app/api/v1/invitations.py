"""
API endpoints for project invitations and team management
"""

import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_project_access, require_project_facilitator
from app.models import User, Project, ProjectMember, ProjectInvitation
from app.services.invitation_service import InvitationService
from app.core.exceptions import ValidationError, PermissionError, NotFoundError
from app.schemas.invitation import (
    InvitationCreate,
    InvitationResponse,
    InvitationListResponse,
    InvitationAcceptResponse,
    ProjectMemberResponse,
    ProjectMembersResponse
)

router = APIRouter()


@router.post(
    "/projects/{project_id}/invite",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite user to project",
    description="Send an invitation to a user to join the project with a specific role"
)
async def invite_user_to_project(
    project_id: uuid.UUID,
    invitation_data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a user to join a project"""
    invitation_service = InvitationService(db)
    
    try:
        invitation = invitation_service.invite_user_to_project(
            project_id=project_id,
            inviter_id=current_user.id,
            email=invitation_data.email,
            role=invitation_data.role,
            message=invitation_data.message
        )
        
        return InvitationResponse.from_invitation(invitation)
        
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/projects/{project_id}/invitations",
    response_model=InvitationListResponse,
    summary="Get project invitations",
    description="Get all invitations for a project (requires member access)"
)
async def get_project_invitations(
    project_id: uuid.UUID,
    include_expired: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all invitations for a project"""
    invitation_service = InvitationService(db)
    
    try:
        invitations = invitation_service.get_project_invitations(
            project_id=project_id,
            requester_id=current_user.id,
            include_expired=include_expired
        )
        
        return InvitationListResponse(invitations=invitations)
        
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/projects/{project_id}/members",
    response_model=ProjectMembersResponse,
    summary="Get project members",
    description="Get all active members of a project"
)
async def get_project_members(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ProjectMembersResponse:
    """Get project members"""
    
    # Check if user has access to this project
    project, membership = require_project_access(project_id, current_user, db)
    
    # Get all active members
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.status == "active"
    ).all()
    
    # Get pending invitations if user has permission
    pending_invitations = []
    if hasattr(membership, 'role') and membership.role in ['facilitator', 'owner']:
        invitation_service = InvitationService(db)
        try:
            pending_invitations = invitation_service.get_project_invitations(
                project_id=project_id,
                requester_id=membership.user_id,
                include_expired=False
            )
        except:
            pass  # Ignore errors getting invitations
    
    member_responses = [
        ProjectMemberResponse.from_member(member) for member in members
    ]
    
    return ProjectMembersResponse(
        members=member_responses,
        pending_invitations=pending_invitations
    )


@router.post(
    "/invitations/{token}/accept",
    response_model=InvitationAcceptResponse,
    summary="Accept invitation",
    description="Accept a project invitation using the invitation token"
)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a project invitation"""
    invitation_service = InvitationService(db)
    
    try:
        membership = invitation_service.accept_invitation(
            token=token,
            user_id=current_user.id
        )
        
        return InvitationAcceptResponse(
            success=True,
            message="Invitation accepted successfully",
            project_id=str(membership.project_id),
            project_title=membership.project.title,
            role=membership.role
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/invitations/{token}/decline",
    response_model=Dict[str, Any],
    summary="Decline invitation",
    description="Decline a project invitation using the invitation token"
)
async def decline_invitation(
    token: str,
    db: Session = Depends(get_db)
):
    """Decline a project invitation"""
    invitation_service = InvitationService(db)
    
    try:
        invitation = invitation_service.decline_invitation(token=token)
        
        return {
            "success": True,
            "message": "Invitation declined",
            "invitation_id": str(invitation.id)
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/invitations/{invitation_id}/cancel",
    response_model=Dict[str, Any],
    summary="Cancel invitation",
    description="Cancel a pending invitation (requires facilitator access)"
)
async def cancel_invitation(
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending invitation"""
    invitation_service = InvitationService(db)
    
    try:
        invitation = invitation_service.cancel_invitation(
            invitation_id=invitation_id,
            canceller_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Invitation cancelled",
            "invitation_id": str(invitation.id)
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/invitations/{invitation_id}/resend",
    response_model=Dict[str, Any],
    summary="Resend invitation",
    description="Resend an invitation email (requires facilitator access)"
)
async def resend_invitation(
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resend an invitation email"""
    invitation_service = InvitationService(db)
    
    try:
        invitation = invitation_service.resend_invitation(
            invitation_id=invitation_id,
            resender_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Invitation email resent",
            "invitation_id": str(invitation.id),
            "expires_at": invitation.expires_at.isoformat()
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    response_model=Dict[str, Any],
    summary="Remove project member",
    description="Remove a member from the project (requires facilitator access)"
)
async def remove_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Remove a member from the project"""
    
    # Check if user has access to this project
    project, membership = require_project_access(project_id, current_user, db)
    
    # Check permissions - must be facilitator or owner
    if membership.role not in ['facilitator', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to remove members"
        )
    
    # Get target member
    target_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.status == "active"
    ).first()
    
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Check if user can manage this member
    from app.core.permissions import ProjectPermissions
    if not ProjectPermissions.can_manage_member(membership.role, target_member.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot remove member with role '{target_member.role}'"
        )
    
    # Cannot remove self (use leave endpoint instead)
    if target_member.user_id == membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from project. Use leave endpoint instead."
        )
    
    # Remove member
    target_member.deactivate()
    db.commit()
    
    return {
        "success": True,
        "message": "Member removed from project",
        "removed_user_id": str(user_id)
    }


@router.put(
    "/projects/{project_id}/members/{user_id}/role",
    response_model=ProjectMemberResponse,
    summary="Update member role",
    description="Update a member's role in the project (requires facilitator access)"
)
async def update_member_role(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ProjectMemberResponse:
    """Update a member's role in the project"""
    
    # Check if user has access to this project
    project, membership = require_project_access(project_id, current_user, db)
    
    new_role = role_data.get("role")
    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role is required"
        )
    
    # Check permissions
    if membership.role not in ['facilitator', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to change member roles"
        )
    
    # Get target member
    target_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.status == "active"
    ).first()
    
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Validate role assignment
    from app.core.permissions import ProjectPermissions
    if not ProjectPermissions.can_assign_role(membership.role, new_role):
        assignable_roles = ProjectPermissions.get_accessible_roles(membership.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot assign role '{new_role}'. You can assign: {assignable_roles}"
        )
    
    # Cannot change own role
    if target_member.user_id == membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Update role
    target_member.role = new_role
    db.commit()
    db.refresh(target_member)
    
    return ProjectMemberResponse.from_member(target_member)


@router.get(
    "/user/invitations",
    response_model=InvitationListResponse,
    summary="Get user invitations",
    description="Get all pending invitations for the current user"
)
async def get_user_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending invitations for the current user"""
    invitation_service = InvitationService(db)
    
    invitations = invitation_service.get_user_invitations(current_user.id)
    
    return InvitationListResponse(invitations=invitations)
