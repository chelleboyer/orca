"""
API endpoints for object cards functionality
"""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_project_access
from app.models import User
from app.services.object_cards_service import ObjectCardsService, CardFilterParams
from app.schemas.object_cards import (
    ObjectCardsResponse, CardFilterRequest, CardStatisticsSchema,
    QuickActionRequest, QuickActionResponse, ObjectCardSchema
)

router = APIRouter()


@router.get(
    "/projects/{project_id}/object-cards",
    response_model=ObjectCardsResponse,
    summary="Get Object Cards",
    description="Get paginated object cards with filtering, sorting, and completion status"
)
async def get_object_cards(
    project_id: uuid.UUID,
    # Query parameters for filtering
    query: str = Query(None, description="Search term for name/definition"),
    has_definition: bool = Query(None, description="Filter by definition presence"),
    has_attributes: bool = Query(None, description="Filter by attribute presence"), 
    has_relationships: bool = Query(None, description="Filter by relationship presence"),
    has_core_attributes: bool = Query(None, description="Filter by core attribute presence"),
    attribute_type: str = Query(None, description="Filter by specific attribute type"),
    min_attributes: int = Query(None, ge=0, description="Minimum number of attributes"),
    max_attributes: int = Query(None, ge=0, description="Maximum number of attributes"),
    layout: str = Query("grid", pattern="^(grid|list)$", description="Card layout type"),
    sort_by: str = Query("name", pattern="^(name|created_at|updated_at|definition|attributes|relationships)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100, description="Number of cards per page"),
    offset: int = Query(0, ge=0, description="Number of cards to skip"),
    include_statistics: bool = Query(True, description="Include project statistics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ObjectCardsResponse:
    """Get object cards with filtering and pagination"""
    
    # Verify user has access to project
    project, membership = require_project_access(project_id, current_user, db)
    
    # Create filter parameters
    filters = CardFilterParams(
        query=query,
        has_definition=has_definition,
        has_attributes=has_attributes,
        has_relationships=has_relationships,
        has_core_attributes=has_core_attributes,
        attribute_type=attribute_type,
        min_attributes=min_attributes,
        max_attributes=max_attributes,
        layout=layout,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    
    # Get cards service
    cards_service = ObjectCardsService(db)
    
    # Get cards data
    cards_data, total = cards_service.get_objects_with_card_data(str(project_id), filters)
    
    # Convert to Pydantic schemas
    cards = [ObjectCardSchema.from_orm(card) for card in cards_data]
    
    # Get statistics if requested
    statistics = None
    if include_statistics:
        stats_data = cards_service.get_card_statistics(str(project_id))
        statistics = CardStatisticsSchema.from_orm(stats_data)
    
    # Build response
    response = ObjectCardsResponse(
        cards=cards,
        total=total,
        limit=limit,
        offset=offset,
        has_next=(offset + limit) < total,
        has_previous=offset > 0,
        total_pages=(total + limit - 1) // limit if total > 0 else 0,
        current_page=(offset // limit) + 1,
        statistics=statistics
    )
    
    return response


@router.get(
    "/projects/{project_id}/object-cards/{object_id}",
    response_model=ObjectCardSchema,
    summary="Get Single Object Card",
    description="Get detailed card data for a specific object"
)
async def get_single_object_card(
    project_id: uuid.UUID,
    object_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ObjectCardSchema:
    """Get single object card data"""
    
    # Verify user has access to project
    project, membership = require_project_access(project_id, current_user, db)
    
    # Get cards service
    cards_service = ObjectCardsService(db)
    
    # Get single card data
    card_data = cards_service.get_single_object_card(str(project_id), str(object_id))
    
    if not card_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object not found"
        )
    
    return ObjectCardSchema.from_orm(card_data)


@router.get(
    "/projects/{project_id}/object-cards/statistics",
    response_model=CardStatisticsSchema,
    summary="Get Object Cards Statistics",
    description="Get completion statistics for all objects in the project"
)
async def get_object_cards_statistics(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CardStatisticsSchema:
    """Get object cards statistics"""
    
    # Verify user has access to project
    project, membership = require_project_access(project_id, current_user, db)
    
    # Get cards service
    cards_service = ObjectCardsService(db)
    
    # Get statistics
    stats_data = cards_service.get_card_statistics(str(project_id))
    
    return CardStatisticsSchema.from_orm(stats_data)


@router.post(
    "/projects/{project_id}/object-cards/quick-action",
    response_model=QuickActionResponse,
    summary="Execute Quick Action",
    description="Execute a quick action on an object card"
)
async def execute_quick_action(
    project_id: uuid.UUID,
    action_request: QuickActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QuickActionResponse:
    """Execute quick action on object card"""
    
    # Verify user has access to project
    project, membership = require_project_access(project_id, current_user, db)
    
    # Get cards service
    cards_service = ObjectCardsService(db)
    
    # Verify object exists and is in this project
    card_data = cards_service.get_single_object_card(str(project_id), action_request.object_id)
    if not card_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object not found"
        )
    
    # Execute the quick action
    response_data = await _execute_quick_action(
        action_request.action,
        action_request.object_id,
        str(project_id),
        card_data,
        current_user,
        db
    )
    
    return QuickActionResponse(**response_data)


async def _execute_quick_action(
    action: str,
    object_id: str,
    project_id: str,
    card_data: Any,  # ObjectCardData
    current_user: User,
    db: Session
) -> Dict[str, Any]:
    """
    Execute specific quick action and return response data
    
    Args:
        action: Action to execute
        object_id: UUID of the object
        project_id: UUID of the project
        card_data: Current object card data
        current_user: Current user
        db: Database session
        
    Returns:
        Dictionary with response data
    """
    base_response = {
        "success": True,
        "action": action,
        "object_id": object_id,
        "message": "",
        "redirect_url": None,
        "data": None
    }
    
    if action == "view":
        base_response.update({
            "message": "Redirecting to object view",
            "redirect_url": f"/dashboard/projects/{project_id}/objects/{object_id}"
        })
        
    elif action == "edit":
        base_response.update({
            "message": "Redirecting to object editor",
            "redirect_url": f"/dashboard/projects/{project_id}/objects/{object_id}/edit"
        })
        
    elif action == "add_definition":
        base_response.update({
            "message": "Redirecting to definition editor",
            "redirect_url": f"/dashboard/projects/{project_id}/objects/{object_id}/edit#definition"
        })
        
    elif action == "add_attributes":
        base_response.update({
            "message": "Redirecting to attribute editor",
            "redirect_url": f"/dashboard/projects/{project_id}/objects/{object_id}/edit#attributes"
        })
        
    elif action == "mark_core_attributes":
        base_response.update({
            "message": "Redirecting to core attribute editor",
            "redirect_url": f"/dashboard/projects/{project_id}/objects/{object_id}/edit#core-attributes"
        })
        
    elif action == "add_relationships":
        base_response.update({
            "message": "Redirecting to relationship editor",
            "redirect_url": f"/dashboard/projects/{project_id}/relationships/create?object_id={object_id}"
        })
        
    elif action == "duplicate":
        # For now, redirect to object creation with copy hint
        base_response.update({
            "message": "Redirecting to object duplication",
            "redirect_url": f"/dashboard/projects/{project_id}/objects/create?copy_from={object_id}"
        })
        
    elif action == "export":
        # For now, redirect to export functionality
        base_response.update({
            "message": "Redirecting to object export",
            "redirect_url": f"/dashboard/projects/{project_id}/objects/{object_id}/export"
        })
        
    else:
        base_response.update({
            "success": False,
            "message": f"Unknown action: {action}"
        })
    
    return base_response
