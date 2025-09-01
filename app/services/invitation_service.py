"""
Service for managing project invitations and team membership
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import User, Project, ProjectMember, ProjectInvitation
from app.core.permissions import ProjectPermissions
from app.core.exceptions import ValidationError, PermissionError, NotFoundError
from app.services.email_service import EmailService


class InvitationService:
    """Service for managing project invitations"""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

    def invite_user_to_project(
        self,
        project_id: uuid.UUID,
        inviter_id: uuid.UUID,
        email: str,
        role: str,
        message: Optional[str] = None
    ) -> ProjectInvitation:
        """
        Invite a user to join a project
        
        Args:
            project_id: The project ID
            inviter_id: ID of user sending invitation
            email: Email address to invite
            role: Role to assign to invited user
            message: Optional custom message
            
        Returns:
            ProjectInvitation object
            
        Raises:
            PermissionError: If inviter lacks permission
            ValidationError: If invitation already exists or other validation error
        """
        # Get project and inviter
        project = self._get_project(project_id)
        inviter = self._get_user(inviter_id)
        
        # Check inviter permissions
        inviter_membership = self._get_user_membership(inviter_id, project_id)
        if not inviter_membership:
            raise PermissionError("Only project members can invite users")
        
        if not ProjectPermissions.has_permission(inviter_membership.role, "invite_users"):
            raise PermissionError("Insufficient permissions to invite users")
        
        # Validate role assignment
        if not ProjectPermissions.can_perform_action(inviter_membership.role, role):
            assignable_roles = ProjectPermissions.get_accessible_roles(inviter_membership.role)
            raise PermissionError(f"Cannot assign role '{role}'. You can assign: {assignable_roles}")
        
        # Check if user is already a member
        existing_member = self._get_user_by_email_membership(email, project_id)
        if existing_member:
            raise ValidationError("User is already a member of this project")
        
        # Check for existing pending invitation
        existing_invitation = self._get_pending_invitation(email, project_id)
        if existing_invitation:
            raise ValidationError("Pending invitation already exists for this email")
        
        # Check if invited user exists in system
        invited_user = self.db.query(User).filter(User.email == email).first()
        
        # Create invitation
        invitation = ProjectInvitation(
            project_id=project_id,
            invited_by=inviter_id,
            invited_user_id=invited_user.id if invited_user else None,
            email=email,
            role=role,
            message=message,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        
        # Send invitation email
        try:
            self._send_invitation_email(invitation)
            invitation.mark_email_sent()
            self.db.commit()
        except Exception as e:
            # Log error but don't fail the invitation creation
            print(f"Failed to send invitation email: {e}")
        
        return invitation

    def accept_invitation(self, token: str, user_id: Optional[uuid.UUID] = None) -> ProjectMember:
        """
        Accept a project invitation
        
        Args:
            token: Invitation token
            user_id: ID of user accepting (for registered users)
            
        Returns:
            ProjectMember object
            
        Raises:
            NotFoundError: If invitation not found
            ValidationError: If invitation cannot be accepted
        """
        invitation = self._get_invitation_by_token(token)
        
        if not invitation.can_be_accepted:
            raise ValidationError("Invitation cannot be accepted (expired, cancelled, or already processed)")
        
        # If user_id provided, update invitation
        if user_id:
            invitation.invited_user_id = user_id
        
        # Check if user is already a member (safety check)
        if invitation.invited_user_id:
            existing_member = self._get_user_membership(invitation.invited_user_id, invitation.project_id)
            if existing_member:
                raise ValidationError("User is already a member of this project")
        
        # Accept invitation
        invitation.accept(invitation.invited_user_id)
        
        # Create project membership
        membership = ProjectMember(
            project_id=invitation.project_id,
            user_id=invitation.invited_user_id,
            role=invitation.role,
            status="active",
            invited_by=invitation.invited_by,
            joined_at=datetime.utcnow()
        )
        
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        
        # Send welcome email
        try:
            self._send_welcome_email(membership)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
        
        return membership

    def decline_invitation(self, token: str) -> ProjectInvitation:
        """
        Decline a project invitation
        
        Args:
            token: Invitation token
            
        Returns:
            Updated ProjectInvitation object
            
        Raises:
            NotFoundError: If invitation not found
            ValidationError: If invitation cannot be declined
        """
        invitation = self._get_invitation_by_token(token)
        
        if not invitation.can_be_accepted:
            raise ValidationError("Invitation cannot be declined (expired, cancelled, or already processed)")
        
        invitation.decline()
        self.db.commit()
        
        return invitation

    def cancel_invitation(
        self,
        invitation_id: uuid.UUID,
        canceller_id: uuid.UUID
    ) -> ProjectInvitation:
        """
        Cancel a pending invitation
        
        Args:
            invitation_id: The invitation ID
            canceller_id: ID of user cancelling invitation
            
        Returns:
            Updated ProjectInvitation object
            
        Raises:
            NotFoundError: If invitation not found
            PermissionError: If user lacks permission to cancel
        """
        invitation = self._get_invitation(invitation_id)
        
        # Check permissions
        canceller_membership = self._get_user_membership(canceller_id, invitation.project_id)
        if not canceller_membership:
            raise PermissionError("Only project members can cancel invitations")
        
        # Can cancel if: inviter themselves, or has manage_invitations permission
        can_cancel = (
            invitation.invited_by == canceller_id or
            ProjectPermissions.has_permission(canceller_membership.role, "manage_invitations")
        )
        
        if not can_cancel:
            raise PermissionError("Insufficient permissions to cancel this invitation")
        
        invitation.cancel()
        self.db.commit()
        
        return invitation

    def get_project_invitations(
        self,
        project_id: uuid.UUID,
        requester_id: uuid.UUID,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all invitations for a project
        
        Args:
            project_id: The project ID
            requester_id: ID of user requesting the list
            include_expired: Whether to include expired invitations
            
        Returns:
            List of invitation dictionaries
            
        Raises:
            PermissionError: If user lacks permission to view invitations
        """
        # Check permissions
        requester_membership = self._get_user_membership(requester_id, project_id)
        if not requester_membership:
            raise PermissionError("Only project members can view invitations")
        
        if not ProjectPermissions.has_permission(requester_membership.role, "view_members"):
            raise PermissionError("Insufficient permissions to view invitations")
        
        # Build query
        query = self.db.query(ProjectInvitation).filter(
            ProjectInvitation.project_id == project_id
        )
        
        if not include_expired:
            query = query.filter(
                or_(
                    ProjectInvitation.status != "expired",
                    and_(
                        ProjectInvitation.status == "pending",
                        ProjectInvitation.expires_at > datetime.utcnow()
                    )
                )
            )
        
        invitations = query.order_by(ProjectInvitation.sent_at.desc()).all()
        
        return [invitation.to_dict() for invitation in invitations]

    def get_user_invitations(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get all pending invitations for a user
        
        Args:
            user_id: The user ID
            
        Returns:
            List of invitation dictionaries
        """
        user = self._get_user(user_id)
        
        # Get invitations by user ID and email
        invitations = self.db.query(ProjectInvitation).filter(
            or_(
                ProjectInvitation.invited_user_id == user_id,
                ProjectInvitation.email == user.email
            ),
            ProjectInvitation.status == "pending",
            ProjectInvitation.expires_at > datetime.utcnow()
        ).order_by(ProjectInvitation.sent_at.desc()).all()
        
        return [invitation.to_dict() for invitation in invitations]

    def resend_invitation(
        self,
        invitation_id: uuid.UUID,
        resender_id: uuid.UUID
    ) -> ProjectInvitation:
        """
        Resend an invitation email
        
        Args:
            invitation_id: The invitation ID
            resender_id: ID of user resending invitation
            
        Returns:
            Updated ProjectInvitation object
            
        Raises:
            NotFoundError: If invitation not found
            PermissionError: If user lacks permission to resend
            ValidationError: If invitation cannot be resent
        """
        invitation = self._get_invitation(invitation_id)
        
        if invitation.status != "pending":
            raise ValidationError("Only pending invitations can be resent")
        
        # Check permissions
        resender_membership = self._get_user_membership(resender_id, invitation.project_id)
        if not resender_membership:
            raise PermissionError("Only project members can resend invitations")
        
        can_resend = (
            invitation.invited_by == resender_id or
            ProjectPermissions.has_permission(resender_membership.role, "manage_invitations")
        )
        
        if not can_resend:
            raise PermissionError("Insufficient permissions to resend this invitation")
        
        # Extend expiration if close to expiring
        if invitation.days_until_expiry <= 1:
            invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Send email
        try:
            self._send_invitation_email(invitation)
            invitation.mark_email_sent()
            self.db.commit()
        except Exception as e:
            raise ValidationError(f"Failed to send invitation email: {e}")
        
        return invitation

    def expire_old_invitations(self) -> int:
        """
        Mark expired invitations as expired (background task)
        
        Returns:
            Number of invitations marked as expired
        """
        expired_invitations = self.db.query(ProjectInvitation).filter(
            ProjectInvitation.status == "pending",
            ProjectInvitation.expires_at < datetime.utcnow()
        ).all()
        
        count = 0
        for invitation in expired_invitations:
            invitation.expire()
            count += 1
        
        if count > 0:
            self.db.commit()
        
        return count

    def send_reminder_emails(self) -> int:
        """
        Send reminder emails for expiring invitations (background task)
        
        Returns:
            Number of reminder emails sent
        """
        invitations_to_remind = self.db.query(ProjectInvitation).filter(
            ProjectInvitation.status == "pending",
            ProjectInvitation.reminder_sent == False,
            ProjectInvitation.expires_at <= datetime.utcnow() + timedelta(days=2),
            ProjectInvitation.expires_at > datetime.utcnow()
        ).all()
        
        count = 0
        for invitation in invitations_to_remind:
            try:
                self._send_reminder_email(invitation)
                invitation.mark_reminder_sent()
                count += 1
            except Exception as e:
                print(f"Failed to send reminder email for invitation {invitation.id}: {e}")
        
        if count > 0:
            self.db.commit()
        
        return count

    # Private helper methods
    
    def _get_project(self, project_id: uuid.UUID) -> Project:
        """Get project or raise NotFoundError"""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.status != "deleted"
        ).first()
        if not project:
            raise NotFoundError("Project not found")
        return project

    def _get_user(self, user_id: uuid.UUID) -> User:
        """Get user or raise NotFoundError"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        return user

    def _get_user_membership(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID
    ) -> Optional[ProjectMember]:
        """Get user's membership in project"""
        return self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
            ProjectMember.status == "active"
        ).first()

    def _get_user_by_email_membership(
        self,
        email: str,
        project_id: uuid.UUID
    ) -> Optional[ProjectMember]:
        """Get user membership by email"""
        return self.db.query(ProjectMember).join(User).filter(
            User.email == email,
            ProjectMember.project_id == project_id,
            ProjectMember.status == "active"
        ).first()

    def _get_pending_invitation(
        self,
        email: str,
        project_id: uuid.UUID
    ) -> Optional[ProjectInvitation]:
        """Get pending invitation for email and project"""
        return self.db.query(ProjectInvitation).filter(
            ProjectInvitation.email == email,
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.status == "pending"
        ).first()

    def _get_invitation(self, invitation_id: uuid.UUID) -> ProjectInvitation:
        """Get invitation or raise NotFoundError"""
        invitation = self.db.query(ProjectInvitation).filter(
            ProjectInvitation.id == invitation_id
        ).first()
        if not invitation:
            raise NotFoundError("Invitation not found")
        return invitation

    def _get_invitation_by_token(self, token: str) -> ProjectInvitation:
        """Get invitation by token or raise NotFoundError"""
        invitation = self.db.query(ProjectInvitation).filter(
            ProjectInvitation.token == token
        ).first()
        if not invitation:
            raise NotFoundError("Invitation not found")
        return invitation

    def _send_invitation_email(self, invitation: ProjectInvitation) -> None:
        """Send invitation email"""
        self.email_service.send_project_invitation(invitation)

    def _send_welcome_email(self, membership: ProjectMember) -> None:
        """Send welcome email to new member"""
        self.email_service.send_welcome_to_project(membership)

    def _send_reminder_email(self, invitation: ProjectInvitation) -> None:
        """Send reminder email for expiring invitation"""
        self.email_service.send_invitation_reminder(invitation)
