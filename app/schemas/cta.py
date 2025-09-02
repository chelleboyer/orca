"""
Pydantic schemas for CTA (Call-to-Action) related API operations.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid

from app.models.cta import CRUDType, CTAStatus


class CTABase(BaseModel):
    """Base CTA schema with common fields."""
    role_id: uuid.UUID = Field(..., description="Role performing the action")
    object_id: uuid.UUID = Field(..., description="Object being acted upon")
    crud_type: CRUDType = Field(..., description="Type of CRUD operation")
    description: Optional[str] = Field(None, max_length=1000, description="CTA description")
    preconditions: Optional[str] = Field(None, max_length=2000, description="Business preconditions")
    postconditions: Optional[str] = Field(None, max_length=2000, description="Business postconditions")
    acceptance_criteria: Optional[str] = Field(None, max_length=2000, description="User story acceptance criteria")
    business_value: Optional[str] = Field(None, max_length=1000, description="Business value statement")
    priority: Optional[int] = Field(1, ge=1, le=5, description="Priority level (1-5)")
    story_points: Optional[int] = Field(None, ge=0, le=100, description="Development effort estimation")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator('preconditions', 'postconditions', 'acceptance_criteria', 'business_value')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate text fields."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class CTACreate(CTABase):
    """Schema for creating CTAs."""
    pass


class CTAUpdate(BaseModel):
    """Schema for updating CTAs."""
    crud_type: Optional[CRUDType] = Field(None, description="Type of CRUD operation")
    description: Optional[str] = Field(None, max_length=1000, description="CTA description")
    preconditions: Optional[str] = Field(None, max_length=2000, description="Business preconditions")
    postconditions: Optional[str] = Field(None, max_length=2000, description="Business postconditions")
    acceptance_criteria: Optional[str] = Field(None, max_length=2000, description="User story acceptance criteria")
    business_value: Optional[str] = Field(None, max_length=1000, description="Business value statement")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority level (1-5)")
    story_points: Optional[int] = Field(None, ge=0, le=100, description="Development effort estimation")
    status: Optional[CTAStatus] = Field(None, description="CTA status")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator('preconditions', 'postconditions', 'acceptance_criteria', 'business_value')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate text fields."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class CTAResponse(BaseModel):
    """Schema for CTA responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    project_id: uuid.UUID
    role_id: uuid.UUID
    object_id: uuid.UUID
    crud_type: str
    description: Optional[str]
    preconditions: Optional[str]
    postconditions: Optional[str]
    acceptance_criteria: Optional[str]
    business_value: Optional[str]
    priority: int
    story_points: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    updated_by: uuid.UUID
    
    # Related entity information
    role_name: str = Field(..., description="Name of the role")
    object_name: str = Field(..., description="Name of the object")
    object_core_noun: Optional[str] = Field(None, description="Core noun of the object")
    
    # Generated content
    user_story: Optional[str] = Field(None, description="Generated user story")
    has_business_rules: bool = Field(False, description="Whether CTA has business rules defined")


class CTAListResponse(BaseModel):
    """Schema for CTA list responses."""
    ctas: List[CTAResponse]
    total: int
    project_id: uuid.UUID


class CTAMatrixCell(BaseModel):
    """Schema for CTA matrix cell data."""
    role_id: uuid.UUID
    object_id: uuid.UUID
    role_name: str
    object_name: str
    ctas: List[CTAResponse]
    has_create: bool = Field(False, description="Has CREATE operation")
    has_read: bool = Field(False, description="Has READ operation")
    has_update: bool = Field(False, description="Has UPDATE operation")
    has_delete: bool = Field(False, description="Has DELETE operation")
    total_ctas: int = Field(0, description="Total number of CTAs in this cell")
    
    
class CTAMatrixRow(BaseModel):
    """Schema for CTA matrix row data."""
    role_id: uuid.UUID
    role_name: str
    cells: List[CTAMatrixCell]
    total_ctas: int = Field(0, description="Total CTAs for this role")


class CTAMatrixResponse(BaseModel):
    """Schema for CTA matrix responses."""
    project_id: uuid.UUID
    roles: List[dict]  # role info
    objects: List[dict]  # object info
    rows: List[CTAMatrixRow]
    total_ctas: int = Field(0, description="Total CTAs in the matrix")
    crud_summary: Dict[str, int] = Field(default_factory=dict, description="CRUD operation counts")


class CTABulkCreateRequest(BaseModel):
    """Schema for bulk creating CTAs."""
    ctas: List[CTACreate] = Field(..., description="List of CTAs to create")
    
    @field_validator('ctas')
    @classmethod
    def validate_ctas(cls, v):
        """Validate CTA list."""
        if not v:
            raise ValueError('CTAs list cannot be empty')
        if len(v) > 100:  # Reasonable limit
            raise ValueError('Cannot create more than 100 CTAs at once')
        return v


class CTABulkCreateResponse(BaseModel):
    """Schema for bulk CTA creation response."""
    created_ctas: List[CTAResponse]
    failed_ctas: List[Dict[str, Any]]  # CTAs that failed to create with error info
    total_created: int
    total_failed: int


class CTASearchRequest(BaseModel):
    """Schema for CTA search requests."""
    role_id: Optional[uuid.UUID] = Field(None, description="Filter by role ID")
    object_id: Optional[uuid.UUID] = Field(None, description="Filter by object ID")
    crud_type: Optional[CRUDType] = Field(None, description="Filter by CRUD type")
    status: Optional[CTAStatus] = Field(None, description="Filter by status")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Filter by priority")
    has_business_rules: Optional[bool] = Field(None, description="Filter by business rules presence")
    search_text: Optional[str] = Field(None, description="Search in description and business rules")
    sort_by: Optional[str] = Field("priority", description="Field to sort by")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")

    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v):
        """Validate sort_by field."""
        allowed_fields = ["priority", "crud_type", "created_at", "updated_at", "status", "story_points"]
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


class CTASearchResponse(BaseModel):
    """Schema for CTA search responses."""
    ctas: List[CTAResponse]
    total: int
    search_criteria: CTASearchRequest


class UserStoryGenerateRequest(BaseModel):
    """Schema for user story generation requests."""
    template_type: Optional[str] = Field("standard", description="User story template type")
    include_acceptance_criteria: bool = Field(True, description="Include acceptance criteria in story")
    include_business_rules: bool = Field(True, description="Include business rules in story")


class UserStoryResponse(BaseModel):
    """Schema for generated user story response."""
    cta_id: uuid.UUID
    user_story: str
    acceptance_criteria: Optional[str]
    business_rules: Optional[str]
    generated_at: datetime


class CTAExportRequest(BaseModel):
    """Schema for CTA export requests."""
    format: str = Field("csv", description="Export format: csv, json, xlsx")
    include_business_rules: bool = Field(True, description="Include business rules in export")
    include_user_stories: bool = Field(False, description="Include generated user stories")
    role_ids: Optional[List[uuid.UUID]] = Field(None, description="Filter by specific roles")
    object_ids: Optional[List[uuid.UUID]] = Field(None, description="Filter by specific objects")
    crud_types: Optional[List[CRUDType]] = Field(None, description="Filter by CRUD types")
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """Validate export format."""
        allowed_formats = ["csv", "json", "xlsx"]
        if v.lower() not in allowed_formats:
            raise ValueError(f'format must be one of {allowed_formats}')
        return v.lower()


class CTAValidationResult(BaseModel):
    """Schema for CTA validation results."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class CTAStatsResponse(BaseModel):
    """Schema for CTA statistics response."""
    project_id: uuid.UUID
    total_ctas: int
    crud_breakdown: Dict[str, int]
    status_breakdown: Dict[str, int]
    priority_breakdown: Dict[str, int]
    roles_with_ctas: int
    objects_with_ctas: int
    ctas_with_business_rules: int
    average_story_points: Optional[float]
    total_story_points: Optional[int]
