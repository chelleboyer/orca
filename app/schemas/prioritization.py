"""
Pydantic schemas for prioritization management
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
import uuid

from app.models.prioritization import PriorityPhase, ItemType


class PrioritizationBase(BaseModel):
    """Base schema for prioritization data"""
    item_type: ItemType = Field(..., description="Type of item being prioritized")
    item_id: str = Field(..., description="UUID of the item being prioritized")
    priority_phase: PriorityPhase = Field(default=PriorityPhase.UNASSIGNED, description="Priority phase assignment")
    score: Optional[int] = Field(None, ge=1, le=10, description="Optional priority score (1-10)")
    position: int = Field(default=0, description="Position within priority phase")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional prioritization notes")


class PrioritizationCreate(PrioritizationBase):
    """Schema for creating a new prioritization"""
    project_id: str = Field(..., description="Project ID")
    assigned_by: Optional[str] = Field(None, description="User ID who assigned the priority")


class PrioritizationUpdate(BaseModel):
    """Schema for updating a prioritization"""
    priority_phase: Optional[PriorityPhase] = Field(None, description="Updated priority phase")
    score: Optional[int] = Field(None, ge=1, le=10, description="Updated priority score")
    position: Optional[int] = Field(None, description="Updated position within phase")
    notes: Optional[str] = Field(None, max_length=1000, description="Updated notes")


class PrioritizationResponse(PrioritizationBase):
    """Schema for prioritization response"""
    id: str
    project_id: str
    assigned_by: Optional[str]
    assigned_at: Optional[datetime]
    updated_at: datetime
    
    # Include item details for convenience
    item_name: Optional[str] = Field(None, description="Name of the prioritized item")
    item_description: Optional[str] = Field(None, description="Description of the prioritized item")
    
    model_config = ConfigDict(from_attributes=True)


class BulkPrioritizationUpdate(BaseModel):
    """Schema for bulk prioritization updates"""
    updates: List[dict] = Field(..., description="List of prioritization updates with item_id and new priority data")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "updates": [
                    {
                        "item_id": "uuid-1", 
                        "item_type": "object", 
                        "priority_phase": "now", 
                        "position": 0
                    },
                    {
                        "item_id": "uuid-2", 
                        "item_type": "cta", 
                        "priority_phase": "next", 
                        "score": 8,
                        "position": 1
                    }
                ]
            }
        }
    )


class PrioritizationFilterParams(BaseModel):
    """Schema for filtering prioritizations"""
    item_type: Optional[ItemType] = Field(None, description="Filter by item type")
    priority_phase: Optional[PriorityPhase] = Field(None, description="Filter by priority phase")
    min_score: Optional[int] = Field(None, ge=1, le=10, description="Minimum score filter")
    max_score: Optional[int] = Field(None, ge=1, le=10, description="Maximum score filter")
    assigned_by: Optional[str] = Field(None, description="Filter by assigner user ID")
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: str = Field(default="position", description="Field to sort by")
    sort_order: str = Field(default="asc", description="Sort order")


class PrioritizationSnapshotBase(BaseModel):
    """Base schema for prioritization snapshots"""
    snapshot_name: str = Field(..., min_length=1, max_length=255, description="Snapshot name")
    description: Optional[str] = Field(None, max_length=1000, description="Snapshot description")


class PrioritizationSnapshotCreate(PrioritizationSnapshotBase):
    """Schema for creating a prioritization snapshot"""
    project_id: str = Field(..., description="Project ID")
    created_by: str = Field(..., description="User ID creating the snapshot")


class PrioritizationSnapshotResponse(PrioritizationSnapshotBase):
    """Schema for prioritization snapshot response"""
    id: str
    project_id: str
    created_by: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PrioritizationStats(BaseModel):
    """Schema for prioritization statistics"""
    total_items: int = Field(..., description="Total items in project")
    prioritized_items: int = Field(..., description="Items with priority assignments")
    
    # Phase counts
    now_count: int = Field(..., description="Items in Now phase")
    next_count: int = Field(..., description="Items in Next phase") 
    later_count: int = Field(..., description="Items in Later phase")
    unassigned_count: int = Field(..., description="Unassigned items")
    
    # By item type
    by_item_type: dict = Field(..., description="Priority counts by item type")
    
    # Score statistics
    average_score: Optional[float] = Field(None, description="Average priority score")
    scored_items: int = Field(..., description="Number of items with scores")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_items": 50,
                "prioritized_items": 35,
                "now_count": 10,
                "next_count": 15,
                "later_count": 10,
                "unassigned_count": 15,
                "by_item_type": {
                    "object": {"now": 5, "next": 8, "later": 4, "unassigned": 8},
                    "cta": {"now": 3, "next": 4, "later": 3, "unassigned": 4},
                    "attribute": {"now": 2, "next": 3, "later": 3, "unassigned": 3}
                },
                "average_score": 6.8,
                "scored_items": 25
            }
        }
    )


class PrioritizationBoard(BaseModel):
    """Schema for prioritization board view"""
    now: List[PrioritizationResponse] = Field(..., description="Items in Now phase")
    next: List[PrioritizationResponse] = Field(..., description="Items in Next phase") 
    later: List[PrioritizationResponse] = Field(..., description="Items in Later phase")
    unassigned: List[PrioritizationResponse] = Field(..., description="Unassigned items")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "now": [],
                "next": [],
                "later": [],
                "unassigned": []
            }
        }
    )


class PaginatedPrioritizations(BaseModel):
    """Schema for paginated prioritization results"""
    items: List[PrioritizationResponse] = Field(..., description="List of prioritizations")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items requested")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "skip": 0,
                "limit": 100
            }
        }
    )
