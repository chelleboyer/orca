"""
CDLL Preview Schemas

Pydantic schemas for CDLL (Cards/Details/Lists/Landings) preview API responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from app.models.prioritization import PriorityPhase


class PreviewType(str, Enum):
    """Types of UI previews that can be generated."""
    CARD = "card"
    DETAIL = "detail"
    LIST = "list"
    LANDING = "landing"


class AttributePreview(BaseModel):
    """Attribute information for previews."""
    name: str
    data_type: str
    value: Optional[str] = None
    required: bool = False
    is_core: Optional[bool] = None


class CTAPreview(BaseModel):
    """CTA information for previews."""
    description: str
    crud_type: str
    business_value: Optional[str] = None
    is_primary: Optional[bool] = None


class SinglePreview(BaseModel):
    """Individual preview (card, detail, list, or landing)."""
    type: PreviewType
    html: str
    # Type-specific data
    title: Optional[str] = None
    subtitle: Optional[str] = None
    definition: Optional[str] = None
    attributes: Optional[List[AttributePreview]] = None
    actions: Optional[List[CTAPreview]] = None
    primary_action: Optional[CTAPreview] = None
    columns: Optional[List[str]] = None
    values: Optional[List[str]] = None
    cta_groups: Optional[Dict[str, List[CTAPreview]]] = None
    core_attributes: Optional[List[AttributePreview]] = None


class CompletionDetail(BaseModel):
    """Completion scoring details for a component."""
    score: int
    status: str  # "complete", "partial", "missing", "excellent", "good", "minimal"
    types: Optional[List[str]] = None  # For CRUD coverage


class CompletionScore(BaseModel):
    """Completion scoring for CDLL generation readiness."""
    total_score: int
    max_score: int
    percentage: int
    grade: str  # A, B, C, D, F
    details: Dict[str, CompletionDetail]


class PreviewWarning(BaseModel):
    """Warning about missing or insufficient data."""
    type: str
    message: str
    suggestion: str


class CDLLPreviewResponse(BaseModel):
    """Complete CDLL preview response for a single object."""
    object_id: str
    object_name: str
    priority_phase: str
    card: SinglePreview
    detail: SinglePreview
    list: SinglePreview
    landing: SinglePreview
    warnings: List[PreviewWarning]
    completion_score: CompletionScore


class ProjectPreviewsResponse(BaseModel):
    """CDLL previews for multiple objects in a project."""
    project_id: str
    priority_filter: Optional[str] = None
    total_objects: int
    previews: List[Dict[str, Any]]  # Can include error objects


class PreviewExportRequest(BaseModel):
    """Request for exporting previews as HTML."""
    object_ids: Optional[List[str]] = Field(
        None, 
        description="Specific object IDs to export. If not provided, exports all objects."
    )
    priority_filter: Optional[PriorityPhase] = Field(
        None,
        description="Filter objects by priority phase (NOW, NEXT, LATER)."
    )
    include_warnings: bool = Field(
        True,
        description="Include warnings in the exported HTML."
    )
    include_completion_scores: bool = Field(
        True,
        description="Include completion scores in the exported HTML."
    )


class CompletionStats(BaseModel):
    """Aggregated completion statistics for a project."""
    project_id: str
    priority_filter: Optional[str] = None
    total_objects: int
    average_score: float
    grade_distribution: Dict[str, int]
    completion_breakdown: Dict[str, float]
    score_range: Dict[str, int]


class ObjectWarningsResponse(BaseModel):
    """Warnings and recommendations for a specific object."""
    object_id: str
    object_name: str
    warnings: List[PreviewWarning]
    completion_score: CompletionScore
    recommendations: List[str]
