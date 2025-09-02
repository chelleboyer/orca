"""
Pydantic schemas for role-related API operations.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid

from app.models.role import RoleStatus


class RoleBase(BaseModel):
    """Base role schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, max_length=1000, description="Role description")
    display_order: Optional[int] = Field(0, ge=0, description="Display order in matrix")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate role name."""
        if not v.strip():
            raise ValueError('Role name cannot be empty or only whitespace')
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate role description."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class RoleCreate(RoleBase):
    """Schema for creating roles."""
    template_type: Optional[str] = Field(None, description="Template type for default roles")


class RoleUpdate(BaseModel):
    """Schema for updating roles."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, max_length=1000, description="Role description")
    display_order: Optional[int] = Field(None, ge=0, description="Display order in matrix")
    status: Optional[RoleStatus] = Field(None, description="Role status")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate role name."""
        if v is not None:
            if not v.strip():
                raise ValueError('Role name cannot be empty or only whitespace')
            return v.strip()
        return v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate role description."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class RoleResponse(BaseModel):
    """Schema for role responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: Optional[str]
    status: str
    display_order: int
    is_template: bool
    template_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    updated_by: uuid.UUID
    cta_count: int = Field(0, description="Number of CTAs using this role")
    can_be_deleted: bool = Field(True, description="Whether role can be safely deleted")


class RoleListResponse(BaseModel):
    """Schema for role list responses."""
    roles: List[RoleResponse]
    total: int
    project_id: uuid.UUID


class RoleReorderRequest(BaseModel):
    """Schema for reordering roles."""
    role_orders: List[dict] = Field(..., description="List of role_id and display_order pairs")

    @field_validator('role_orders')
    @classmethod
    def validate_role_orders(cls, v):
        """Validate role order data."""
        if not v:
            raise ValueError('Role orders cannot be empty')
        
        for item in v:
            if not isinstance(item, dict):
                raise ValueError('Each role order item must be a dictionary')
            if 'role_id' not in item or 'display_order' not in item:
                raise ValueError('Each role order item must have role_id and display_order')
            
            # Validate UUID format
            try:
                uuid.UUID(str(item['role_id']))
            except ValueError:
                raise ValueError(f'Invalid role_id format: {item["role_id"]}')
            
            # Validate display_order
            if not isinstance(item['display_order'], int) or item['display_order'] < 0:
                raise ValueError(f'display_order must be a non-negative integer: {item["display_order"]}')
        
        return v


class DefaultRoleTemplate(BaseModel):
    """Schema for default role templates."""
    name: str
    description: str
    template_type: str
    display_order: int


class DefaultRolesResponse(BaseModel):
    """Schema for default role templates response."""
    templates: List[DefaultRoleTemplate]


class RoleBulkCreateRequest(BaseModel):
    """Schema for creating multiple roles from templates."""
    template_types: List[str] = Field(..., description="List of template types to create")
    
    @field_validator('template_types')
    @classmethod
    def validate_template_types(cls, v):
        """Validate template types."""
        if not v:
            raise ValueError('Template types cannot be empty')
        
        valid_types = ['user', 'admin', 'guest', 'manager', 'support']
        for template_type in v:
            if template_type not in valid_types:
                raise ValueError(f'Invalid template type: {template_type}. Must be one of {valid_types}')
        
        return v


class RoleBulkCreateResponse(BaseModel):
    """Schema for bulk role creation response."""
    created_roles: List[RoleResponse]
    skipped_roles: List[dict]  # Roles that already exist
    total_created: int
    total_skipped: int


class RoleSearchRequest(BaseModel):
    """Schema for role search requests."""
    name: Optional[str] = Field(None, description="Filter by role name (partial match)")
    status: Optional[RoleStatus] = Field(None, description="Filter by role status")
    template_type: Optional[str] = Field(None, description="Filter by template type")
    has_ctas: Optional[bool] = Field(None, description="Filter by whether role has CTAs")
    sort_by: Optional[str] = Field("display_order", description="Field to sort by")
    sort_order: Optional[str] = Field("asc", description="Sort order: asc or desc")

    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v):
        """Validate sort_by field."""
        allowed_fields = ["name", "display_order", "created_at", "updated_at", "status"]
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of {allowed_fields}')
        return v

    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        """Validate sort_order field."""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()


class RoleSearchResponse(BaseModel):
    """Schema for role search responses."""
    roles: List[RoleResponse]
    total: int
    search_criteria: RoleSearchRequest
