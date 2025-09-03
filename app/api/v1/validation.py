"""
API endpoints for project validation and completeness analysis.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.validation_service import ValidationService
from app.schemas.validation import (
    ValidationSummaryResponse,
    ObjectValidationDetailed,
    ValidationGapsResponse,
    ValidationStatsResponse
)


router = APIRouter()


@router.get("/{project_id}/validation", response_model=ValidationSummaryResponse)
async def get_project_validation_summary(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive validation summary for entire project.
    
    Returns complete analysis including:
    - Overall completion percentage
    - Export readiness assessment
    - Dimension scores (objects, attributes, CTAs, relationships, prioritization)
    - Individual object validation results
    - Actionable recommendations
    """
    try:
        validation_service = ValidationService(db)
        summary = validation_service.get_project_validation_summary(project_id)
        return ValidationSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation analysis failed: {str(e)}")


@router.get("/{project_id}/objects/{object_id}/validation", response_model=ObjectValidationDetailed)
async def get_object_validation_details(
    project_id: str,
    object_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed validation information for a specific object.
    
    Returns comprehensive analysis including:
    - Completion score breakdown
    - Specific warnings and recommendations
    - Object data summary
    - Export readiness status
    """
    try:
        validation_service = ValidationService(db)
        details = validation_service.get_object_validation_details(project_id, object_id)
        return ObjectValidationDetailed(**details)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Object validation failed: {str(e)}")


@router.get("/{project_id}/validation/gaps", response_model=ValidationGapsResponse)
async def get_validation_gaps(
    project_id: str,
    priority: Optional[str] = Query(None, regex="^(now|next|later)$", description="Filter by priority phase"),
    db: Session = Depends(get_db)
):
    """
    Get gaps and missing elements across the project.
    
    Identifies:
    - Objects with missing or inadequate definitions
    - Objects with insufficient core attributes
    - Objects missing primary CTAs
    - Isolated objects (no relationships)
    - Other completeness gaps
    
    Optionally filter by priority phase (now/next/later).
    """
    try:
        validation_service = ValidationService(db)
        gaps = validation_service.get_validation_gaps(project_id, priority)
        return ValidationGapsResponse(**gaps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


@router.get("/{project_id}/validation/stats", response_model=ValidationStatsResponse)
async def get_validation_stats(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get high-level validation statistics for dashboard widgets.
    
    Returns summary metrics:
    - Overall completion percentage
    - Export readiness status
    - Object count
    - Total gaps count
    - Last validation timestamp
    """
    try:
        validation_service = ValidationService(db)
        summary = validation_service.get_project_validation_summary(project_id)
        
        stats = {
            "project_id": project_id,
            "overall_completion": summary["overall_completion"],
            "export_ready": summary["export_ready"],
            "object_count": summary["object_count"],
            "gaps_count": sum(len(gaps) for gaps in summary.get("gaps", {}).values()) if "gaps" in summary else 0,
            "last_validation": summary["validation_timestamp"]
        }
        
        return ValidationStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation stats failed: {str(e)}")


@router.get("/{project_id}/validation/export-readiness")
async def get_export_readiness_assessment(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get focused export readiness assessment.
    
    Returns specific analysis for development handoff:
    - Export ready status
    - Blocking issues
    - Readiness percentage
    - Critical dimension analysis
    """
    try:
        validation_service = ValidationService(db)
        summary = validation_service.get_project_validation_summary(project_id)
        
        return {
            "project_id": project_id,
            "export_readiness": summary["export_readiness_details"],
            "overall_completion": summary["overall_completion"],
            "dimension_summary": {
                name: {
                    "completion_percentage": data.completion_percentage,
                    "status": data.status
                }
                for name, data in summary["dimension_scores"].items()
            },
            "recommendations": [
                rec for rec in summary["recommendations"] 
                if rec["priority"] == "high"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export readiness assessment failed: {str(e)}")


# Future enhancement endpoints
@router.get("/{project_id}/validation/rules")
async def get_validation_rules(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current validation rules and thresholds.
    Future enhancement: Allow customization per project.
    """
    validation_service = ValidationService(db)
    return validation_service._get_validation_rules_summary()


@router.post("/{project_id}/validation/rules")
async def update_validation_rules(
    project_id: str,
    # config: ValidationConfigRequest,
    db: Session = Depends(get_db)
):
    """
    Update validation rules and thresholds for project.
    Future enhancement: Configurable validation rules.
    """
    raise HTTPException(status_code=501, detail="Configurable validation rules not yet implemented")


@router.post("/{project_id}/validation/refresh")
async def refresh_validation_cache(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Refresh validation analysis (future caching enhancement).
    Currently validation is calculated in real-time.
    """
    try:
        validation_service = ValidationService(db)
        summary = validation_service.get_project_validation_summary(project_id)
        
        return {
            "project_id": project_id,
            "refreshed_at": summary["validation_timestamp"],
            "overall_completion": summary["overall_completion"],
            "export_ready": summary["export_ready"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation refresh failed: {str(e)}")
