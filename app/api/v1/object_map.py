"""
API endpoints for object map visualization
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.services.object_map_service import ObjectMapService
from app.core.exceptions import NotFoundError, PermissionError

router = APIRouter()


@router.get("/projects/{project_id}/object-map", response_model=Dict[str, Any])
def get_object_map_data(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive object map data for visualization"""
    service = ObjectMapService(db)
    
    try:
        map_data = service.get_object_map_data(project_id)
        return map_data
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get object map data: {str(e)}"
        )


@router.put("/projects/{project_id}/object-map/object-position/{object_id}")
def update_object_position(
    project_id: uuid.UUID,
    object_id: uuid.UUID,
    x: float = Query(..., description="X coordinate"),
    y: float = Query(..., description="Y coordinate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update object position in the map"""
    service = ObjectMapService(db)
    
    try:
        success = service.update_object_position(project_id, object_id, x, y)
        return {"success": success, "object_id": str(object_id), "position": {"x": x, "y": y}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update object position: {str(e)}"
        )


@router.post("/projects/{project_id}/object-map/auto-layout")
def apply_auto_layout(
    project_id: uuid.UUID,
    algorithm: str = Query("force_directed", description="Layout algorithm"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply auto-layout algorithm to arrange objects"""
    service = ObjectMapService(db)
    
    try:
        result = service.auto_layout_objects(project_id, algorithm)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply auto-layout: {str(e)}"
        )


@router.get("/projects/{project_id}/object-map/export")
def export_object_map(
    project_id: uuid.UUID,
    format: str = Query("json", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export object map data in various formats"""
    service = ObjectMapService(db)
    
    try:
        export_data = service.export_map_data(project_id, format)
        return export_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export object map: {str(e)}"
        )
