"""
Prioritization models for Now/Next/Later development phases
Supports prioritizing objects, CTAs, and attributes independently
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.models.base import Base


class PriorityPhase(enum.Enum):
    """Development priority phases"""
    NOW = "now"
    NEXT = "next"
    LATER = "later"
    UNASSIGNED = "unassigned"


class ItemType(enum.Enum):
    """Types of items that can be prioritized"""
    OBJECT = "object"
    CTA = "cta"
    ATTRIBUTE = "attribute"
    RELATIONSHIP = "relationship"


class Prioritization(Base):
    """
    Prioritization assignment for project items
    Supports Now/Next/Later prioritization with optional scoring
    """
    __tablename__ = "prioritizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    # Item identification
    item_type = Column(SqlEnum(ItemType), nullable=False)
    item_id = Column(String, nullable=False)  # UUID of the prioritized item
    
    # Prioritization data
    priority_phase = Column(SqlEnum(PriorityPhase), default=PriorityPhase.UNASSIGNED)
    score = Column(Integer, nullable=True)  # 1-10 optional scoring
    position = Column(Integer, default=0)  # Order within phase
    
    # Metadata
    notes = Column(Text, nullable=True)
    assigned_by = Column(String, nullable=True)  # User ID
    assigned_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="prioritizations")
    
    def __repr__(self):
        return f"<Prioritization(item_type={self.item_type.value}, item_id={self.item_id}, phase={self.priority_phase.value})>"


class PrioritizationSnapshot(Base):
    """
    Historical snapshots of prioritization states
    Enables tracking priority changes over time
    """
    __tablename__ = "prioritization_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    # Snapshot metadata
    snapshot_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(String, nullable=False)  # User ID
    created_at = Column(DateTime, default=func.now())
    
    # Snapshot data (JSON serialized prioritization state)
    snapshot_data = Column(Text, nullable=False)  # JSON
    
    # Relationships
    project = relationship("Project", back_populates="prioritization_snapshots")
    
    def __repr__(self):
        return f"<PrioritizationSnapshot(name={self.snapshot_name}, project_id={self.project_id})>"


# Extend Project model with prioritization relationships
# This will be done in the migration or via import
