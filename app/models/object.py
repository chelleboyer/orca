"""
Object model for OOUX domain objects.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Object(Base):
    """
    Core domain object in the OOUX methodology.
    Represents the fundamental entities in a domain model.
    """
    __tablename__ = "objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    definition = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="objects")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    synonyms = relationship("ObjectSynonym", back_populates="object", cascade="all, delete-orphan")
    states = relationship("ObjectState", back_populates="object", cascade="all, delete-orphan")
    
    # Relationship connections for NOM matrix
    outgoing_relationships = relationship("Relationship", foreign_keys="Relationship.source_object_id", back_populates="source_object", cascade="all, delete-orphan")
    incoming_relationships = relationship("Relationship", foreign_keys="Relationship.target_object_id", back_populates="target_object", cascade="all, delete-orphan")
    
    # CTA connections for behavioral matrix
    ctas = relationship("CTA", back_populates="object", cascade="all, delete-orphan")
    
    # Attribute connections for object properties
    object_attributes = relationship("ObjectAttribute", back_populates="object", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_objects_project_name', 'project_id', 'name'),
        Index('ix_objects_created_at', 'created_at'),
        Index('ix_objects_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<Object(id={self.id}, name='{self.name}', project_id={self.project_id})>"


class ObjectSynonym(Base):
    """
    Alternative names for objects to support team vocabulary alignment.
    """
    __tablename__ = "object_synonyms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    object_id = Column(UUID(as_uuid=True), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    synonym = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    object = relationship("Object", back_populates="synonyms")
    creator = relationship("User")
    
    # Indexes for performance and constraints
    __table_args__ = (
        Index('ix_object_synonyms_object_synonym', 'object_id', 'synonym'),
        Index('ix_object_synonyms_synonym', 'synonym'),
    )

    def __repr__(self):
        return f"<ObjectSynonym(id={self.id}, synonym='{self.synonym}', object_id={self.object_id})>"


class ObjectState(Base):
    """
    Possible states for objects with lifecycle management.
    Optional feature - not all objects need states.
    """
    __tablename__ = "object_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    object_id = Column(UUID(as_uuid=True), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    state_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(String(50), nullable=True)  # For ordering states in UI
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    object = relationship("Object", back_populates="states")
    creator = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_object_states_object_name', 'object_id', 'state_name'),
        Index('ix_object_states_order', 'object_id', 'order_index'),
    )

    def __repr__(self):
        return f"<ObjectState(id={self.id}, state_name='{self.state_name}', object_id={self.object_id})>"
