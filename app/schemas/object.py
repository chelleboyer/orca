"""
Pydantic schemas for object-related API operations.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import uuid


class ObjectSynonymCreate(BaseModel):
    """Schema for creating object synonyms."""
    synonym: str = Field(..., min_length=1, max_length=255, description="Alternative name for the object")


class ObjectSynonymResponse(BaseModel):
    """Schema for object synonym responses."""
    id: uuid.UUID
    synonym: str
    created_at: datetime
    created_by: uuid.UUID

    class Config:
        from_attributes = True


class ObjectStateCreate(BaseModel):
    """Schema for creating object states."""
    state_name: str = Field(..., min_length=1, max_length=100, description="Name of the state")
    description: Optional[str] = Field(None, max_length=500, description="Optional description of the state")
    order_index: Optional[int] = Field(None, description="Order index for state display")


class ObjectStateResponse(BaseModel):
    """Schema for object state responses."""
    id: uuid.UUID
    state_name: str
    description: Optional[str]
    order_index: Optional[int]
    created_at: datetime
    created_by: uuid.UUID

    class Config:
        from_attributes = True


class ObjectCreate(BaseModel):
    """Schema for creating objects."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the object")
    definition: Optional[str] = Field(None, max_length=2000, description="Definition or description of the object")

    @validator('name')
    def validate_name(cls, v):
        """Validate object name."""
        if not v.strip():
            raise ValueError('Object name cannot be empty or whitespace only')
        # Remove extra whitespace
        return ' '.join(v.split())


class ObjectUpdate(BaseModel):
    """Schema for updating objects."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the object")
    definition: Optional[str] = Field(None, max_length=2000, description="Definition or description of the object")

    @validator('name')
    def validate_name(cls, v):
        """Validate object name."""
        if v is not None:
            if not v.strip():
                raise ValueError('Object name cannot be empty or whitespace only')
            # Remove extra whitespace
            return ' '.join(v.split())
        return v


class ObjectResponse(BaseModel):
    """Schema for object responses."""
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    definition: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    updated_by: uuid.UUID
    synonyms: List[ObjectSynonymResponse] = []
    states: List[ObjectStateResponse] = []

    class Config:
        from_attributes = True


class ObjectListResponse(BaseModel):
    """Schema for object list responses with metadata."""
    id: uuid.UUID
    name: str
    definition: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    updated_by: uuid.UUID
    synonym_count: int = 0
    state_count: int = 0
    has_definition: bool = False

    class Config:
        from_attributes = True

    @validator('has_definition', pre=True, always=True)
    def set_has_definition(cls, v, values):
        """Set has_definition based on definition field."""
        definition = values.get('definition')
        return bool(definition and definition.strip())


class ObjectSearchRequest(BaseModel):
    """Schema for object search requests."""
    query: Optional[str] = Field(None, max_length=255, description="Search query for name, definition, or synonyms")
    sort_by: Optional[str] = Field("name", description="Field to sort by: name, created_at, updated_at")
    sort_order: Optional[str] = Field("asc", description="Sort order: asc or desc")
    limit: Optional[int] = Field(50, ge=1, le=100, description="Number of results to return")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort_by field."""
        allowed_fields = ["name", "created_at", "updated_at"]
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of {allowed_fields}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort_order field."""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()


class ObjectSearchResponse(BaseModel):
    """Schema for paginated object search responses."""
    objects: List[ObjectListResponse]
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
