"""
Invitation models for project team management
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class ProjectInvitation(BaseModel):
    """
    Project invitation model for managing team member invitations
    """
    
    __tablename__ = "project_invitations"

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id"), 
        nullable=False,
        index=True
    )
    invited_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id"), 
        nullable=True,
        index=True
    )
    
    # Invitation details
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Invitation content
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status and timing
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    declined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Email tracking
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project")
    inviter = relationship("User", foreign_keys=[invited_by])
    invited_user = relationship("User", foreign_keys=[invited_user_id])
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("role IN ('facilitator', 'contributor', 'viewer')", name="check_invitation_role"),
        CheckConstraint("status IN ('pending', 'accepted', 'declined', 'expired', 'cancelled')", name="check_invitation_status"),
        CheckConstraint("expires_at > sent_at", name="check_invitation_expiry"),
        CheckConstraint("message IS NULL OR char_length(message) <= 500", name="check_message_length"),
        Index("idx_invitations_project_id", "project_id"),
        Index("idx_invitations_email", "email"),
        Index("idx_invitations_token", "token"),
        Index("idx_invitations_status", "status"),
        Index("idx_invitations_expires_at", "expires_at"),
        # Prevent duplicate pending invitations
        Index("idx_unique_pending_invitation", "project_id", "email", "status", 
              unique=True, postgresql_where="status = 'pending'"),
    )

    def __init__(self, **kwargs):
        # Set default expiration to 7 days from now if not provided
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.utcnow() + timedelta(days=7)
        
        # Generate unique token if not provided
        if 'token' not in kwargs:
            kwargs['token'] = self._generate_token()
        
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ProjectInvitation(id='{self.id}', email='{self.email}', project_id='{self.project_id}', status='{self.status}')>"

    def __str__(self) -> str:
        return f"Invitation for {self.email} to {self.project.title if self.project else 'Unknown Project'}"

    @staticmethod
    def _generate_token() -> str:
        """Generate a unique invitation token"""
        import secrets
        return secrets.token_urlsafe(32)

    @property
    def is_pending(self) -> bool:
        """Check if invitation is pending"""
        return self.status == "pending"

    @property
    def is_accepted(self) -> bool:
        """Check if invitation has been accepted"""
        return self.status == "accepted"

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        return self.status == "expired" or (self.status == "pending" and datetime.utcnow() > self.expires_at)

    @property
    def is_cancelled(self) -> bool:
        """Check if invitation has been cancelled"""
        return self.status == "cancelled"

    @property
    def can_be_accepted(self) -> bool:
        """Check if invitation can still be accepted"""
        return self.status == "pending" and not self.is_expired

    @property
    def days_until_expiry(self) -> int:
        """Get number of days until invitation expires"""
        if self.expires_at:
            delta = self.expires_at - datetime.utcnow()
            return max(0, delta.days)
        return 0

    def accept(self, user_id: Optional[uuid.UUID] = None) -> None:
        """Accept the invitation"""
        if not self.can_be_accepted:
            raise ValueError("Invitation cannot be accepted (expired, cancelled, or already processed)")
        
        self.status = "accepted"
        self.accepted_at = datetime.utcnow()
        if user_id:
            self.invited_user_id = user_id

    def decline(self) -> None:
        """Decline the invitation"""
        if not self.can_be_accepted:
            raise ValueError("Invitation cannot be declined (expired, cancelled, or already processed)")
        
        self.status = "declined"
        self.declined_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel the invitation"""
        if self.status not in ["pending"]:
            raise ValueError("Only pending invitations can be cancelled")
        
        self.status = "cancelled"

    def expire(self) -> None:
        """Mark invitation as expired"""
        if self.status == "pending":
            self.status = "expired"

    def mark_email_sent(self) -> None:
        """Mark that invitation email has been sent"""
        self.email_sent = True
        self.email_sent_at = datetime.utcnow()

    def mark_reminder_sent(self) -> None:
        """Mark that reminder email has been sent"""
        self.reminder_sent = True
        self.reminder_sent_at = datetime.utcnow()

    def should_send_reminder(self) -> bool:
        """Check if reminder should be sent (pending, not reminded, expires in 2 days)"""
        return (
            self.status == "pending" and 
            not self.reminder_sent and 
            self.days_until_expiry <= 2 and 
            self.days_until_expiry > 0
        )

    def to_dict(self) -> dict:
        """Convert invitation to dictionary for API responses"""
        return {
            "invitation_id": str(self.id),
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "message": self.message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "declined_at": self.declined_at.isoformat() if self.declined_at else None,
            "invited_by": {
                "id": str(self.inviter.id),
                "name": self.inviter.name,
                "email": self.inviter.email
            } if self.inviter else None,
            "days_until_expiry": self.days_until_expiry,
            "can_be_accepted": self.can_be_accepted
        }
