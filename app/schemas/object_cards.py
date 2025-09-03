"""
Pydantic schemas for object cards functionality
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CoreAttributeSchema(BaseModel):
    """Schema for core attribute display in cards"""
    id: str
    name: str
    data_type: str
    display_type: str
    value: Optional[str] = None
    is_core: bool = True

    class Config:
        from_attributes = True


class CompletionStatusSchema(BaseModel):
    """Schema for object completion status"""
    has_definition: bool
    has_attributes: bool
    has_core_attributes: bool
    has_relationships: bool
    completion_score: float = Field(ge=0.0, le=100.0)

    class Config:
        from_attributes = True


class ObjectCardSchema(BaseModel):
    """Schema for object card display"""
    id: str
    name: str
    definition: str
    definition_summary: str
    core_attributes: List[CoreAttributeSchema]
    all_attributes_count: int = Field(ge=0)
    relationship_count: int = Field(ge=0)
    completion_status: CompletionStatusSchema
    quick_actions: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CardFilterRequest(BaseModel):
    """Request schema for filtering object cards"""
    query: Optional[str] = Field(None, max_length=255, description="Search term for name/definition")
    has_definition: Optional[bool] = Field(None, description="Filter by definition presence")
    has_attributes: Optional[bool] = Field(None, description="Filter by attribute presence")
    has_relationships: Optional[bool] = Field(None, description="Filter by relationship presence")
    has_core_attributes: Optional[bool] = Field(None, description="Filter by core attribute presence")
    attribute_type: Optional[str] = Field(None, description="Filter by specific attribute type")
    min_attributes: Optional[int] = Field(None, ge=0, description="Minimum number of attributes")
    max_attributes: Optional[int] = Field(None, ge=0, description="Maximum number of attributes")
    layout: str = Field("grid", pattern="^(grid|list)$", description="Card layout type")
    sort_by: str = Field("name", pattern="^(name|created_at|updated_at|definition|attributes|relationships)$")
    sort_order: str = Field("asc", pattern="^(asc|desc)$")
    limit: int = Field(20, ge=1, le=100, description="Number of cards per page")
    offset: int = Field(0, ge=0, description="Number of cards to skip")

    @validator('max_attributes')
    def validate_max_attributes(cls, v, values):
        """Ensure max_attributes >= min_attributes if both provided"""
        if v is not None and 'min_attributes' in values and values['min_attributes'] is not None:
            if v < values['min_attributes']:
                raise ValueError('max_attributes must be >= min_attributes')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "query": "user",
                "has_definition": True,
                "has_core_attributes": True,
                "layout": "grid",
                "sort_by": "name",
                "sort_order": "asc",
                "limit": 20,
                "offset": 0
            }
        }


class CardStatisticsSchema(BaseModel):
    """Schema for object cards statistics"""
    total_objects: int = Field(ge=0)
    with_definitions: int = Field(ge=0)
    with_attributes: int = Field(ge=0)
    with_core_attributes: int = Field(ge=0)
    with_relationships: int = Field(ge=0)
    completion_percentages: Dict[str, float]
    average_completion: float = Field(ge=0.0, le=100.0)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "total_objects": 25,
                "with_definitions": 20,
                "with_attributes": 18,
                "with_core_attributes": 12,
                "with_relationships": 15,
                "completion_percentages": {
                    "definitions": 80.0,
                    "attributes": 72.0,
                    "core_attributes": 48.0,
                    "relationships": 60.0
                },
                "average_completion": 65.0
            }
        }


class ObjectCardsResponse(BaseModel):
    """Response schema for object cards listing"""
    cards: List[ObjectCardSchema]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    has_next: bool
    has_previous: bool
    total_pages: int = Field(ge=0)
    current_page: int = Field(ge=1)
    statistics: Optional[CardStatisticsSchema] = None

    @validator('has_next')
    def calculate_has_next(cls, v, values):
        """Calculate if there are more pages"""
        if 'total' in values and 'limit' in values and 'offset' in values:
            return (values['offset'] + values['limit']) < values['total']
        return v

    @validator('has_previous')
    def calculate_has_previous(cls, v, values):
        """Calculate if there are previous pages"""
        if 'offset' in values:
            return values['offset'] > 0
        return v

    @validator('total_pages')
    def calculate_total_pages(cls, v, values):
        """Calculate total number of pages"""
        if 'total' in values and 'limit' in values:
            import math
            return math.ceil(values['total'] / values['limit']) if values['total'] > 0 else 0
        return v

    @validator('current_page')
    def calculate_current_page(cls, v, values):
        """Calculate current page number"""
        if 'offset' in values and 'limit' in values:
            return (values['offset'] // values['limit']) + 1
        return v

    class Config:
        from_attributes = True


class QuickActionRequest(BaseModel):
    """Request schema for quick actions on object cards"""
    action: str = Field(..., pattern="^(view|edit|add_definition|add_attributes|mark_core_attributes|add_relationships|duplicate|export)$")
    object_id: str = Field(..., description="UUID of the object")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "add_definition",
                "object_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class QuickActionResponse(BaseModel):
    """Response schema for quick action execution"""
    success: bool
    action: str
    object_id: str
    message: str
    redirect_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "action": "add_definition",
                "object_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Redirecting to object definition editor",
                "redirect_url": "/projects/proj-id/objects/obj-id/edit#definition",
                "data": None
            }
        }
