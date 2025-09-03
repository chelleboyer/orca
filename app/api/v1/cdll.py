"""
CDLL Preview API Endpoints

Provides endpoints for generating and exporting Cards, Details, Lists, 
and Landings previews for objects in the OOUX system.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.cdll_preview_service import CDLLPreviewService
from app.models.prioritization import PriorityPhase
from app.schemas.cdll import (
    CDLLPreviewResponse,
    ProjectPreviewsResponse,
    PreviewExportRequest
)

router = APIRouter(prefix="/api/v1/cdll", tags=["CDLL Previews"])


@router.get("/{project_id}/objects/{object_id}/previews", response_model=CDLLPreviewResponse)
async def get_object_previews(
    project_id: str,
    object_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate CDLL previews for a specific object.
    
    Returns Card, Detail, List, and Landing previews along with
    warnings and completion scoring.
    """
    
    try:
        cdll_service = CDLLPreviewService(db)
        previews = cdll_service.generate_object_previews(project_id, object_id)
        
        return CDLLPreviewResponse(**previews)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate previews: {str(e)}")


@router.get("/{project_id}/previews", response_model=ProjectPreviewsResponse)
async def get_project_previews(
    project_id: str,
    priority_filter: Optional[PriorityPhase] = Query(None, description="Filter by priority phase"),
    db: Session = Depends(get_db)
):
    """
    Generate CDLL previews for all objects in a project.
    
    Optionally filter by priority phase (NOW, NEXT, LATER).
    Returns previews for all matching objects.
    """
    
    try:
        cdll_service = CDLLPreviewService(db)
        previews = cdll_service.generate_project_previews(project_id, priority_filter)
        
        return ProjectPreviewsResponse(
            project_id=project_id,
            priority_filter=priority_filter.value if priority_filter else None,
            total_objects=len(previews),
            previews=previews
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate project previews: {str(e)}")


@router.post("/{project_id}/export")
async def export_previews_html(
    project_id: str,
    export_request: PreviewExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export CDLL previews as standalone HTML file.
    
    Generates a complete HTML document with embedded CSS
    containing all preview data for the specified objects.
    """
    
    try:
        cdll_service = CDLLPreviewService(db)
        
        # Generate previews for requested objects
        if export_request.object_ids:
            # Generate previews for specific objects
            preview_data = []
            for object_id in export_request.object_ids:
                try:
                    preview = cdll_service.generate_object_previews(project_id, object_id)
                    preview_data.append(preview)
                except ValueError:
                    # Skip objects that don't exist
                    continue
        else:
            # Generate previews for all objects (optionally filtered by priority)
            preview_data = cdll_service.generate_project_previews(
                project_id, 
                export_request.priority_filter
            )
        
        if not preview_data:
            raise HTTPException(
                status_code=404, 
                detail="No objects found matching the export criteria"
            )
        
        # Generate HTML export
        html_content = cdll_service.export_previews_html(project_id, preview_data)
        
        # Return as downloadable HTML file
        headers = {
            "Content-Disposition": f"attachment; filename=cdll-previews-{project_id}.html",
            "Content-Type": "text/html"
        }
        
        return Response(content=html_content, headers=headers, media_type="text/html")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export previews: {str(e)}")


@router.get("/{project_id}/completion-stats")
async def get_completion_stats(
    project_id: str,
    priority_filter: Optional[PriorityPhase] = Query(None, description="Filter by priority phase"),
    db: Session = Depends(get_db)
):
    """
    Get completion statistics for CDLL generation readiness.
    
    Returns aggregated completion scores and grade distribution
    for objects in the project.
    """
    
    try:
        cdll_service = CDLLPreviewService(db)
        previews = cdll_service.generate_project_previews(project_id, priority_filter)
        
        # Calculate aggregate statistics
        total_objects = len(previews)
        
        if total_objects == 0:
            return {
                "project_id": project_id,
                "priority_filter": priority_filter.value if priority_filter else None,
                "total_objects": 0,
                "average_score": 0,
                "grade_distribution": {},
                "completion_breakdown": {}
            }
        
        # Extract completion scores
        completion_scores = []
        grade_counts = {}
        
        for preview in previews:
            if "completion_score" in preview:
                score_data = preview["completion_score"]
                completion_scores.append(score_data["percentage"])
                
                grade = score_data["grade"]
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        average_score = sum(completion_scores) / len(completion_scores) if completion_scores else 0
        
        # Calculate completion breakdown by component
        component_scores = {
            "definition": [],
            "core_attributes": [],
            "primary_ctas": [],
            "crud_coverage": []
        }
        
        for preview in previews:
            if "completion_score" in preview and "details" in preview["completion_score"]:
                details = preview["completion_score"]["details"]
                for component, scores in component_scores.items():
                    if component in details:
                        scores.append(details[component]["score"])
        
        component_averages = {
            component: sum(scores) / len(scores) if scores else 0
            for component, scores in component_scores.items()
        }
        
        return {
            "project_id": project_id,
            "priority_filter": priority_filter.value if priority_filter else None,
            "total_objects": total_objects,
            "average_score": round(average_score, 1),
            "grade_distribution": grade_counts,
            "completion_breakdown": component_averages,
            "score_range": {
                "min": min(completion_scores) if completion_scores else 0,
                "max": max(completion_scores) if completion_scores else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate completion stats: {str(e)}")


@router.get("/{project_id}/objects/{object_id}/warnings")
async def get_object_warnings(
    project_id: str,
    object_id: str,
    db: Session = Depends(get_db)
):
    """
    Get warnings for a specific object's CDLL generation readiness.
    
    Returns detailed warnings about missing or insufficient data
    that could impact preview quality.
    """
    
    try:
        cdll_service = CDLLPreviewService(db)
        
        # Get object data for warning analysis
        obj_data = cdll_service._get_object_with_data(project_id, object_id)
        if not obj_data:
            raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
        
        # Generate warnings
        warnings = cdll_service._generate_warnings(obj_data)
        completion_score = cdll_service._calculate_completion_score(obj_data)
        
        return {
            "object_id": object_id,
            "object_name": obj_data["name"],
            "warnings": warnings,
            "completion_score": completion_score,
            "recommendations": _generate_recommendations(warnings, completion_score)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze object warnings: {str(e)}")


def _generate_recommendations(
    warnings: List[dict], 
    completion_score: dict
) -> List[str]:
    """Generate actionable recommendations based on warnings and completion score."""
    
    recommendations = []
    
    # Priority recommendations based on completion score
    if completion_score["percentage"] < 60:
        recommendations.append(
            "⚠️ Critical: This object has significant gaps that will impact UI generation quality. "
            "Focus on the highest-impact improvements first."
        )
    elif completion_score["percentage"] < 80:
        recommendations.append(
            "📈 Good progress! A few improvements will significantly enhance preview quality."
        )
    else:
        recommendations.append(
            "✅ Excellent! This object is well-prepared for high-quality UI generation."
        )
    
    # Specific recommendations based on warnings
    warning_types = {warning["type"] for warning in warnings}
    
    if "missing_definition" in warning_types:
        recommendations.append(
            "📝 Add a clear, comprehensive definition describing what this object represents "
            "and its role in your system."
        )
    
    if "insufficient_core_attributes" in warning_types:
        recommendations.append(
            "🏷️ Identify and mark 3-5 key attributes as 'core' - these are the most important "
            "pieces of information users need to see about this object."
        )
    
    if "no_primary_ctas" in warning_types:
        recommendations.append(
            "⚡ Mark the most common user actions as 'primary' CTAs to highlight key functionality "
            "in generated interfaces."
        )
    
    if "no_read_cta" in warning_types:
        recommendations.append(
            "👁️ Add a READ CTA describing how users can view details about this object "
            "(e.g., 'View Profile', 'See Details')."
        )
    
    # Component-specific recommendations
    details = completion_score.get("details", {})
    
    if details.get("definition", {}).get("status") in ["missing", "partial"]:
        recommendations.append(
            "✍️ Expand the object definition to at least 20 characters with meaningful description."
        )
    
    if details.get("crud_coverage", {}).get("score", 0) < 15:
        missing_cruds = set(["CREATE", "READ", "UPDATE", "DELETE"]) - set(
            details.get("crud_coverage", {}).get("types", [])
        )
        if missing_cruds:
            recommendations.append(
                f"🔧 Consider adding CTAs for missing CRUD operations: {', '.join(missing_cruds)}."
            )
    
    return recommendations
