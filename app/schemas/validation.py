"""
Pydantic schemas for validation API responses.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ValidationRulesSummary(BaseModel):
    """Summary of validation rules and thresholds."""
    completion_thresholds: Dict[str, int]
    scoring_weights: Dict[str, int]
    configurable: bool


class DimensionScore(BaseModel):
    """Score data for a single OOUX dimension."""
    total: int
    completion_percentage: float
    status: str
    
    # Dimension-specific fields
    with_definition: Optional[int] = None
    core: Optional[int] = None
    primary: Optional[int] = None
    potential: Optional[int] = None


class ObjectValidation(BaseModel):
    """Validation result for a single object."""
    object_id: str
    object_name: str
    completion_score: float
    completion_grade: str
    warnings_count: int
    export_ready: bool


class ObjectValidationDetailed(ObjectValidation):
    """Detailed validation result for a single object."""
    completion_breakdown: Dict[str, Any]
    warnings: List[Dict[str, str]]
    object_data: Dict[str, Any]
    recommendations: List[Dict[str, str]]


class ExportReadiness(BaseModel):
    """Export readiness assessment."""
    ready: bool
    overall_completion: float
    min_completion_threshold: float
    objects_ready: int
    objects_ready_percentage: float
    min_objects_ready_threshold: float
    critical_dimensions_complete: bool
    blocking_issues: List[str]


class ProjectRecommendation(BaseModel):
    """Project improvement recommendation."""
    type: str
    priority: str
    title: str
    description: str
    action: str


class ValidationSummaryResponse(BaseModel):
    """Complete project validation summary."""
    project_id: str
    validation_timestamp: str
    overall_completion: float
    export_ready: bool
    export_readiness_details: ExportReadiness
    dimension_scores: Dict[str, DimensionScore]
    object_count: int
    object_validations: List[ObjectValidation]
    recommendations: List[ProjectRecommendation]
    validation_rules: ValidationRulesSummary


class ValidationGap(BaseModel):
    """Individual validation gap."""
    object_id: str
    object_name: str
    issue: str
    recommendation: str
    core_count: Optional[int] = None


class ValidationGapsResponse(BaseModel):
    """Comprehensive gap analysis."""
    project_id: str
    priority_filter: Optional[str]
    gap_summary: Dict[str, int]
    gaps: Dict[str, List[ValidationGap]]
    total_gaps: int


class ValidationStatsResponse(BaseModel):
    """High-level validation statistics."""
    project_id: str
    overall_completion: float
    export_ready: bool
    object_count: int
    gaps_count: int
    last_validation: str


# Request schemas for configuration (future enhancement)
class ValidationConfigRequest(BaseModel):
    """Request to update validation configuration."""
    completion_thresholds: Optional[Dict[str, int]] = None
    scoring_weights: Optional[Dict[str, int]] = None
    custom_rules: Optional[List[Dict[str, Any]]] = None
