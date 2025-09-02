"""
Pydantic schemas for relationship-related API operations.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import uuid

from app.models.relationship import CardinalityType


class RelationshipCreate(BaseModel):
    """Schema for creating relationships."""
    source_object_id: uuid.UUID = Field(..., description="Source object UUID")
    target_object_id: uuid.UUID = Field(..., description="Target object UUID")
    cardinality: CardinalityType = Field(CardinalityType.ONE_TO_MANY, description="Relationship cardinality")
    forward_label: Optional[str] = Field(None, max_length=255, description="Label for source -> target direction")
    reverse_label: Optional[str] = Field(None, max_length=255, description="Label for target -> source direction")
    is_bidirectional: bool = Field(False, description="Whether relationship is bidirectional")
    description: Optional[str] = Field(None, max_length=1000, description="Additional relationship description")
    strength: Optional[str] = Field("normal", description="Relationship strength: weak, normal, strong")

    @validator('strength')
    def validate_strength(cls, v):
        """Validate relationship strength."""
        allowed_strengths = ["weak", "normal", "strong"]
        if v not in allowed_strengths:
            raise ValueError(f'Strength must be one of {allowed_strengths}')
        return v

    @validator('source_object_id', 'target_object_id')
    def validate_objects_different(cls, v, values):
        """Validate that source and target objects are different."""
        if 'source_object_id' in values and v == values['source_object_id']:
            raise ValueError('Source and target objects must be different (no self-references)')
        return v


class RelationshipUpdate(BaseModel):
    """Schema for updating relationships."""
    cardinality: Optional[CardinalityType] = Field(None, description="Relationship cardinality")
    forward_label: Optional[str] = Field(None, max_length=255, description="Label for source -> target direction")
    reverse_label: Optional[str] = Field(None, max_length=255, description="Label for target -> source direction")
    is_bidirectional: Optional[bool] = Field(None, description="Whether relationship is bidirectional")
    description: Optional[str] = Field(None, max_length=1000, description="Additional relationship description")
    strength: Optional[str] = Field(None, description="Relationship strength: weak, normal, strong")

    @validator('strength')
    def validate_strength(cls, v):
        """Validate relationship strength."""
        if v is not None:
            allowed_strengths = ["weak", "normal", "strong"]
            if v not in allowed_strengths:
                raise ValueError(f'Strength must be one of {allowed_strengths}')
        return v


class RelationshipResponse(BaseModel):
    """Schema for relationship responses."""
    id: uuid.UUID
    project_id: uuid.UUID
    source_object_id: uuid.UUID
    target_object_id: uuid.UUID
    cardinality: CardinalityType
    forward_label: Optional[str]
    reverse_label: Optional[str]
    is_bidirectional: bool
    description: Optional[str]
    strength: str
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    updated_by: uuid.UUID

    class Config:
        from_attributes = True


class MatrixCellData(BaseModel):
    """Schema for individual matrix cell data."""
    source_object_id: uuid.UUID
    target_object_id: uuid.UUID
    relationship: Optional[RelationshipResponse] = None
    is_self_reference: bool = False
    can_edit: bool = True
    is_locked: bool = False
    locked_by: Optional[uuid.UUID] = None


class MatrixObjectData(BaseModel):
    """Schema for object data in matrix context."""
    id: uuid.UUID
    name: str
    definition: Optional[str]
    synonym_count: int = 0
    outgoing_relationship_count: int = 0
    incoming_relationship_count: int = 0


class NOMMatrixResponse(BaseModel):
    """Schema for complete NOM matrix data."""
    project_id: uuid.UUID
    objects: List[MatrixObjectData]
    matrix_data: List[List[MatrixCellData]]
    total_objects: int
    total_relationships: int
    matrix_completion_percentage: float

    @validator('matrix_completion_percentage')
    def validate_completion_percentage(cls, v):
        """Ensure completion percentage is between 0 and 100."""
        return max(0.0, min(100.0, v))


class RelationshipSearchRequest(BaseModel):
    """Schema for relationship search requests."""
    source_object_id: Optional[uuid.UUID] = Field(None, description="Filter by source object")
    target_object_id: Optional[uuid.UUID] = Field(None, description="Filter by target object")
    cardinality: Optional[CardinalityType] = Field(None, description="Filter by cardinality")
    strength: Optional[str] = Field(None, description="Filter by strength")
    is_bidirectional: Optional[bool] = Field(None, description="Filter by bidirectional flag")
    sort_by: Optional[str] = Field("created_at", description="Field to sort by")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")
    limit: Optional[int] = Field(50, ge=1, le=100, description="Number of results to return")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort_by field."""
        allowed_fields = ["created_at", "updated_at", "cardinality", "strength"]
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of {allowed_fields}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort_order field."""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()

    @validator('strength')
    def validate_strength(cls, v):
        """Validate strength filter."""
        if v is not None:
            allowed_strengths = ["weak", "normal", "strong"]
            if v not in allowed_strengths:
                raise ValueError(f'Strength must be one of {allowed_strengths}')
        return v


class RelationshipSearchResponse(BaseModel):
    """Schema for paginated relationship search responses."""
    relationships: List[RelationshipResponse]
    total: int
    limit: int
    offset: int
    has_more: bool

    @validator('has_more', pre=True, always=True)
    def set_has_more(cls, v, values):
        """Calculate if there are more results."""
        total = values.get('total', 0)
        offset = values.get('offset', 0)
        limit = values.get('limit', 50)
        return (offset + limit) < total


class RelationshipLockRequest(BaseModel):
    """Schema for requesting relationship locks."""
    source_object_id: uuid.UUID
    target_object_id: uuid.UUID
    session_id: str = Field(..., min_length=1, max_length=255)
    lock_type: str = Field("edit", description="Type of lock: edit, view, bulk")

    @validator('lock_type')
    def validate_lock_type(cls, v):
        """Validate lock type."""
        allowed_types = ["edit", "view", "bulk"]
        if v not in allowed_types:
            raise ValueError(f'Lock type must be one of {allowed_types}')
        return v


class RelationshipLockResponse(BaseModel):
    """Schema for relationship lock responses."""
    id: uuid.UUID
    source_object_id: uuid.UUID
    target_object_id: uuid.UUID
    locked_by: uuid.UUID
    locked_at: datetime
    expires_at: datetime
    session_id: str
    lock_type: str
    minutes_remaining: float

    class Config:
        from_attributes = True


class PresenceUpdateRequest(BaseModel):
    """Schema for updating user presence."""
    current_object_id: Optional[uuid.UUID] = None
    current_activity: str = Field("viewing", description="Current activity: viewing, editing, navigating")
    matrix_row: Optional[int] = Field(None, ge=0, description="Current matrix row")
    matrix_col: Optional[int] = Field(None, ge=0, description="Current matrix column")

    @validator('current_activity')
    def validate_activity(cls, v):
        """Validate current activity."""
        allowed_activities = ["viewing", "editing", "navigating"]
        if v not in allowed_activities:
            raise ValueError(f'Activity must be one of {allowed_activities}')
        return v


class PresenceResponse(BaseModel):
    """Schema for user presence responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    session_id: str
    last_seen: datetime
    current_object_id: Optional[uuid.UUID]
    current_activity: str
    matrix_row: Optional[int]
    matrix_col: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True


class CollaborationSummary(BaseModel):
    """Schema for collaboration summary in projects."""
    active_users: List[PresenceResponse]
    active_locks: List[RelationshipLockResponse]
    recent_changes: List[RelationshipResponse]
    total_active_users: int
    total_active_locks: int
