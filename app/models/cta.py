"""
CTA (Call-to-Action) model for OOUX behavioral mapping.
"""
from datetime import datetime
from typing import Optional
import uuid
from enum import Enum

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship as sql_relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CRUDType(str, Enum):
    """Enumeration for CRUD operation types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    NONE = "none"  # For actions that don't fit CRUD


class CTAStatus(str, Enum):
    """Enumeration for CTA status types."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class CTA(Base):
    """
    Call-to-Action model representing role-object interactions.
    Maps specific actions that roles can perform on objects.
    """
    __tablename__ = "ctas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    object_id = Column(UUID(as_uuid=True), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # CTA properties
    description = Column(Text, nullable=True)
    crud_type = Column(String(20), default=CRUDType.NONE, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)  # Primary action for this role-object
    
    # Ordering within role-object cell
    display_order = Column(Integer, default=0, nullable=False)
    
    # Business context
    preconditions = Column(Text, nullable=True)  # What must be true before action
    postconditions = Column(Text, nullable=True)  # What changes after action
    business_rules = Column(Text, nullable=True)  # Additional business rules
    
    # User story context
    user_story = Column(Text, nullable=True)  # As a [role], I want to [verb] [object]...
    acceptance_criteria = Column(Text, nullable=True)  # Specific acceptance criteria
    
    # Status and metadata
    status = Column(String(20), default=CTAStatus.ACTIVE, nullable=False, index=True)
    priority = Column(Integer, default=1, nullable=False)  # 1-5 priority level
    story_points = Column(Integer, nullable=True)  # Development effort estimation
    business_value = Column(String(1000), nullable=True)  # Business value statement
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    project = sql_relationship("Project", back_populates="ctas")
    role = sql_relationship("Role", back_populates="ctas")
    object = sql_relationship("Object", back_populates="ctas")
    creator = sql_relationship("User", foreign_keys=[created_by])
    updater = sql_relationship("User", foreign_keys=[updated_by])
    
    # Table constraints and indexes
    __table_args__ = (
        # Performance indexes
        Index('ix_ctas_role_object', 'role_id', 'object_id'),
        Index('ix_ctas_project_role', 'project_id', 'role_id'),
        Index('ix_ctas_project_object', 'project_id', 'object_id'),
        Index('ix_ctas_crud_type', 'crud_type'),
        Index('ix_ctas_is_primary', 'is_primary'),
        Index('ix_ctas_priority', 'priority'),
        Index('ix_ctas_display_order', 'role_id', 'object_id', 'display_order'),
        Index('ix_ctas_created_at', 'created_at'),
        Index('ix_ctas_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<CTA(id={self.id}, crud_type='{self.crud_type}', role_id={self.role_id}, object_id={self.object_id})>"

    def __str__(self):
        return f"CTA: {self.crud_type} {self.object_id} as {self.role_id}"
