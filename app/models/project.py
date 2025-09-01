"""
Project models for project management and team collaboration
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class Project(BaseModel):
    """
    Project model representing an OOUX project workspace
    """
    
    __tablename__ = "projects"

    # Project metadata
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    
    # Activity tracking
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Project ownership and status
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id"), 
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), 
        default="active", 
        nullable=False,
        index=True
    )
    
    # Flexible data storage
    project_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived', 'deleted')", name="check_project_status"),
        CheckConstraint("char_length(title) >= 3", name="check_title_min_length"),
        CheckConstraint("char_length(title) <= 100", name="check_title_max_length"),
        CheckConstraint("description IS NULL OR char_length(description) <= 1000", name="check_description_length"),
        Index("idx_projects_created_by", "created_by"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_updated_at", "updated_at"),
        Index("idx_projects_last_activity", "last_activity"),
    )

    def __repr__(self) -> str:
        return f"<Project(id='{self.id}', title='{self.title}', slug='{self.slug}')>"

    def __str__(self) -> str:
        return self.title

    @property
    def is_active(self) -> bool:
        """Check if project is in active status"""
        return self.status == "active"

    @property
    def is_archived(self) -> bool:
        """Check if project is archived"""
        return self.status == "archived"

    def get_member_count(self) -> int:
        """Get total number of active project members"""
        return len([m for m in self.members if m.is_active])

    def get_facilitators(self) -> List["ProjectMember"]:
        """Get all facilitator members"""
        return [m for m in self.members if m.role == "facilitator" and m.is_active]

    def get_member_by_user_id(self, user_id: uuid.UUID) -> Optional["ProjectMember"]:
        """Get project member by user ID"""
        return next((m for m in self.members if m.user_id == user_id and m.is_active), None)

    def has_member(self, user_id: uuid.UUID) -> bool:
        """Check if user is an active member of the project"""
        return self.get_member_by_user_id(user_id) is not None

    def get_user_role(self, user_id: uuid.UUID) -> Optional[str]:
        """Get user's role in the project"""
        member = self.get_member_by_user_id(user_id)
        return member.role if member else None

    def update_activity(self) -> None:
        """Update the last activity timestamp"""
        self.last_activity = datetime.utcnow()


class ProjectMember(BaseModel):
    """
    Project membership model representing user roles within projects
    """
    
    __tablename__ = "project_members"

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Membership details
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    
    # Invitation tracking
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    invited_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id"), 
        nullable=True
    )
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="project_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("role IN ('facilitator', 'contributor', 'viewer')", name="check_member_role"),
        CheckConstraint("status IN ('pending', 'active', 'inactive')", name="check_member_status"),
        Index("idx_project_members_project_id", "project_id"),
        Index("idx_project_members_user_id", "user_id"),
        Index("idx_project_members_role", "role"),
        Index("idx_project_members_status", "status"),
        # Unique constraint to prevent duplicate memberships
        Index("idx_unique_project_user", "project_id", "user_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ProjectMember(project_id='{self.project_id}', user_id='{self.user_id}', role='{self.role}')>"

    def __str__(self) -> str:
        return f"{self.user.name if self.user else 'Unknown'} - {self.role}"

    @property
    def is_active(self) -> bool:
        """Check if membership is active"""
        return self.status == "active"

    @property
    def is_pending(self) -> bool:
        """Check if membership is pending acceptance"""
        return self.status == "pending"

    @property
    def is_facilitator(self) -> bool:
        """Check if member has facilitator role"""
        return self.role == "facilitator"

    @property
    def is_contributor(self) -> bool:
        """Check if member has contributor role"""
        return self.role == "contributor"

    @property
    def is_viewer(self) -> bool:
        """Check if member has viewer role"""
        return self.role == "viewer"

    def activate(self) -> None:
        """Activate the membership"""
        if self.status == "pending":
            self.status = "active"
            self.joined_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the membership"""
        self.status = "inactive"
