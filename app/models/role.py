"""
Role model for OOUX project-specific user roles.
"""
from datetime import datetime
from typing import Optional, List
import uuid
from enum import Enum

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship as sql_relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RoleStatus(str, Enum):
    """Enumeration for role status types."""
    ACTIVE = "active"
    ARCHIVED = "archived"


class Role(Base):
    """
    Role model representing domain-specific user roles within projects.
    Used for Call-to-Action Matrix mapping.
    """
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Role properties
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=RoleStatus.ACTIVE, nullable=False, index=True)
    
    # Ordering for matrix display
    display_order = Column(Integer, default=0, nullable=False, index=True)
    
    # Template information
    is_template = Column(Boolean, default=False, nullable=False)  # For default roles
    template_type = Column(String(50), nullable=True)  # user, admin, guest, etc.
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    project = sql_relationship("Project", back_populates="roles")
    creator = sql_relationship("User", foreign_keys=[created_by])
    updater = sql_relationship("User", foreign_keys=[updated_by])
    ctas = sql_relationship("CTA", back_populates="role", cascade="all, delete-orphan")
    
    # Table constraints and indexes
    __table_args__ = (
        # Unique role names per project
        Index('ix_roles_unique_name_per_project', 'project_id', 'name', unique=True),
        # Performance indexes
        Index('ix_roles_project_status', 'project_id', 'status'),
        Index('ix_roles_project_order', 'project_id', 'display_order'),
        Index('ix_roles_template', 'is_template', 'template_type'),
        Index('ix_roles_created_at', 'created_at'),
        Index('ix_roles_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', project_id={self.project_id})>"

    def __str__(self):
        return self.name

    @property
    def is_active(self) -> bool:
        """Check if role is active"""
        return self.status == RoleStatus.ACTIVE.value

    @property
    def is_archived(self) -> bool:
        """Check if role is archived"""
        return self.status == RoleStatus.ARCHIVED.value

    def can_be_deleted(self) -> bool:
        """Check if role can be safely deleted (no CTAs depend on it)"""
        return len(self.ctas) == 0

    def get_cta_count(self) -> int:
        """Get count of CTAs associated with this role"""
        return len(self.ctas) if self.ctas else 0

    def archive(self) -> None:
        """Archive the role instead of deleting if it has CTAs"""
        self.status = RoleStatus.ARCHIVED.value

    def activate(self) -> None:
        """Reactivate an archived role"""
        self.status = RoleStatus.ACTIVE.value


# Default role templates for projects
DEFAULT_ROLES = {
    'user': {
        'name': 'User',
        'description': 'Standard user with basic access and interactions',
        'template_type': 'user',
        'display_order': 1
    },
    'admin': {
        'name': 'Admin',
        'description': 'Administrator with full system access and management capabilities',
        'template_type': 'admin',
        'display_order': 2
    },
    'guest': {
        'name': 'Guest',
        'description': 'Guest user with limited read-only access',
        'template_type': 'guest',
        'display_order': 3
    },
    'manager': {
        'name': 'Manager',
        'description': 'Manager with supervisory and approval capabilities',
        'template_type': 'manager',
        'display_order': 4
    },
    'support': {
        'name': 'Support',
        'description': 'Support staff with assistance and troubleshooting capabilities',
        'template_type': 'support',
        'display_order': 5
    }
}
