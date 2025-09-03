"""
Pydantic schemas for attribute management
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Any
from datetime import datetime
import uuid

from app.models.attribute import AttributeType


class AttributeBase(BaseModel):
    """Base schema for attribute data"""
    name: str = Field(..., min_length=1, max_length=255, description="Attribute name")
    description: Optional[str] = Field(None, max_length=1000, description="Attribute description")
    data_type: AttributeType = Field(default=AttributeType.TEXT, description="Data type of the attribute")
    is_core: bool = Field(default=False, description="Whether this is a core attribute")
    reference_object_id: Optional[uuid.UUID] = Field(None, description="Referenced object ID for reference types")
    list_options: Optional[str] = Field(None, description="JSON string of options for list types")
    is_active: bool = Field(default=True, description="Whether the attribute is active")


class AttributeCreate(AttributeBase):
    """Schema for creating a new attribute"""
    project_id: uuid.UUID = Field(..., description="Project ID this attribute belongs to")


class AttributeUpdate(BaseModel):
    """Schema for updating an attribute"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    data_type: Optional[AttributeType] = None
    is_core: Optional[bool] = None
    reference_object_id: Optional[uuid.UUID] = None
    list_options: Optional[str] = None
    is_active: Optional[bool] = None


class AttributeResponse(AttributeBase):
    """Schema for attribute responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    display_type: str


class AttributeListResponse(BaseModel):
    """Schema for attribute list responses"""
    attributes: List[AttributeResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


# Object Attribute Schemas
class ObjectAttributeBase(BaseModel):
    """Base schema for object attribute values"""
    value: Optional[str] = Field(None, description="String representation of the attribute value")


class ObjectAttributeCreate(ObjectAttributeBase):
    """Schema for creating an object attribute value"""
    object_id: uuid.UUID = Field(..., description="Object ID")
    attribute_id: uuid.UUID = Field(..., description="Attribute ID")


class ObjectAttributeUpdate(BaseModel):
    """Schema for updating an object attribute value"""
    value: Optional[str] = None


class ObjectAttributeResponse(ObjectAttributeBase):
    """Schema for object attribute responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    object_id: uuid.UUID
    attribute_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    typed_value: Any  # The value converted to the appropriate Python type


class BulkAttributeCreate(BaseModel):
    """Schema for bulk creating attributes"""
    attributes: List[AttributeCreate] = Field(..., description="List of attributes to create")


class BulkAttributeUpdate(BaseModel):
    """Schema for bulk updating object attributes"""
    updates: List[dict] = Field(..., description="List of attribute updates with object_id, attribute_id, and value")


class AttributeFilterParams(BaseModel):
    """Schema for filtering attributes"""
    name: Optional[str] = Field(None, description="Filter by attribute name (partial match)")
    data_type: Optional[AttributeType] = Field(None, description="Filter by data type")
    is_core: Optional[bool] = Field(None, description="Filter by core status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    reference_object_id: Optional[uuid.UUID] = Field(None, description="Filter by referenced object")
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: str = Field(default="name", description="Field to sort by")
    sort_order: str = Field(default="asc", description="Sort order")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v


class AttributeStatsResponse(BaseModel):
    """Schema for attribute statistics"""
    total_attributes: int
    core_attributes: int
    active_attributes: int
    by_type: dict[str, int]
    usage_stats: dict[str, int]  # How many objects use each attribute
