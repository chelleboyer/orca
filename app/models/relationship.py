"""
Relationship model for OOUX object relationships and NOM matrix.
"""
from datetime import datetime, timedelta
from typing import Optional
import uuid
from enum import Enum

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship as sql_relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CardinalityType(str, Enum):
    """Enumeration for relationship cardinality types."""
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_MANY = "N:M"


class Relationship(Base):
    """
    Relationship model representing connections between objects in the NOM matrix.
    Supports cardinality, directional labels, and bidirectional relationships.
    """
    __tablename__ = "relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Object relationships
    source_object_id = Column(UUID(as_uuid=True), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    target_object_id = Column(UUID(as_uuid=True), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationship properties
    cardinality = Column(SQLEnum(CardinalityType), nullable=False, default=CardinalityType.ONE_TO_MANY)
    forward_label = Column(String(255), nullable=True)  # Source -> Target label
    reverse_label = Column(String(255), nullable=True)  # Target -> Source label
    is_bidirectional = Column(Boolean, default=False, nullable=False)
    
    # Additional metadata
    description = Column(Text, nullable=True)
    strength = Column(String(20), default="normal", nullable=False)  # weak, normal, strong
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    project = sql_relationship("Project", back_populates="relationships")
    source_object = sql_relationship("Object", foreign_keys=[source_object_id], back_populates="outgoing_relationships")
    target_object = sql_relationship("Object", foreign_keys=[target_object_id], back_populates="incoming_relationships")
    creator = sql_relationship("User", foreign_keys=[created_by])
    updater = sql_relationship("User", foreign_keys=[updated_by])
    
    # Table constraints and indexes
    __table_args__ = (
        # Prevent duplicate relationships between same objects
        Index('ix_relationships_unique_pair', 'source_object_id', 'target_object_id', unique=True),
        # Performance indexes
        Index('ix_relationships_project_source', 'project_id', 'source_object_id'),
        Index('ix_relationships_project_target', 'project_id', 'target_object_id'),
        Index('ix_relationships_cardinality', 'cardinality'),
        Index('ix_relationships_bidirectional', 'is_bidirectional'),
        Index('ix_relationships_created_at', 'created_at'),
        Index('ix_relationships_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<Relationship(id={self.id}, {self.source_object_id} -> {self.target_object_id}, {self.cardinality})>"

    def __str__(self):
        return f"Relationship {self.id}"

    def get_matrix_summary(self) -> dict:
        """Get a summary suitable for matrix cell display."""
        return {
            "id": str(self.id),
            "cardinality": "1:N",  # Default cardinality
            "forward_label": None,
            "reverse_label": None,
            "is_bidirectional": False,
            "strength": "normal"
        }


class RelationshipLock(Base):
    """
    Model for tracking active editing locks on relationships.
    Prevents simultaneous editing conflicts in collaborative environments.
    """
    __tablename__ = "relationship_locks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    relationship_id = Column(UUID(as_uuid=True), ForeignKey("relationships.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # For new relationships being created
    source_object_id = Column(UUID(as_uuid=True), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    target_object_id = Column(UUID(as_uuid=True), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Lock details
    locked_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    locked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Lock metadata
    session_id = Column(String(255), nullable=False, index=True)
    lock_type = Column(String(20), default="edit", nullable=False)  # edit, view, bulk
    
    # Relationships
    relationship = sql_relationship("Relationship")
    source_object = sql_relationship("Object", foreign_keys=[source_object_id])
    target_object = sql_relationship("Object", foreign_keys=[target_object_id])
    user = sql_relationship("User")
    
    # Table constraints
    __table_args__ = (
        # Only one lock per object pair at a time
        Index('ix_relationship_locks_unique_pair', 'source_object_id', 'target_object_id', unique=True),
        # Performance indexes
        Index('ix_relationship_locks_user', 'locked_by'),
        Index('ix_relationship_locks_expires', 'expires_at'),
        Index('ix_relationship_locks_session', 'session_id'),
    )

    def __repr__(self):
        return f"<RelationshipLock(id={self.id}, {self.source_object_id} -> {self.target_object_id}, locked_by={self.locked_by})>"


class UserPresence(Base):
    """
    Model for tracking user presence and activity in the NOM matrix.
    Enables real-time collaborative awareness.
    """
    __tablename__ = "user_presence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Presence details
    session_id = Column(String(255), nullable=False, index=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Current activity
    current_object_id = Column(UUID(as_uuid=True), ForeignKey("objects.id", ondelete="SET NULL"), nullable=True)
    current_activity = Column(String(50), default="viewing", nullable=False)  # viewing, editing, navigating
    
    # Location in matrix
    matrix_row = Column(Integer, nullable=True)
    matrix_col = Column(Integer, nullable=True)
    
    # Relationships
    project = sql_relationship("Project")
    user = sql_relationship("User")
    current_object = sql_relationship("Object")
    
    # Table constraints
    __table_args__ = (
        # One presence record per user per project
        Index('ix_user_presence_unique', 'project_id', 'user_id', unique=True),
        # Performance indexes
        Index('ix_user_presence_session', 'session_id'),
        Index('ix_user_presence_last_seen', 'last_seen'),
        Index('ix_user_presence_activity', 'current_activity'),
    )

    def __repr__(self):
        return f"<UserPresence(user_id={self.user_id}, project_id={self.project_id}, activity={self.current_activity})>"
