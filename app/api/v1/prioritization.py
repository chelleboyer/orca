"""
API router for prioritization endpoints
Handles Now/Next/Later prioritization for objects, CTAs, attributes, and relationships
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.prioritization import PriorityPhase, ItemType
from app.services.prioritization_service import PrioritizationService
from app.schemas.prioritization import (
    PrioritizationResponse, PrioritizationCreate, PrioritizationUpdate,
    PrioritizationFilterParams, PrioritizationSnapshotResponse, PrioritizationSnapshotCreate,
    BulkPrioritizationUpdate, PrioritizationBoard, PrioritizationStats,
    PaginatedPrioritizations
)

router = APIRouter(prefix="/projects/{project_id}/prioritizations", tags=["prioritization"])


@router.post("", response_model=PrioritizationResponse, status_code=status.HTTP_201_CREATED)
async def create_prioritization(
    project_id: str,
    prioritization_data: PrioritizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new prioritization entry"""
    
    # Set project_id from path
    prioritization_data.project_id = project_id
    prioritization_data.assigned_by = str(current_user.id)
    
    service = PrioritizationService(db)
    prioritization = service.create_prioritization(prioritization_data)
    
    return PrioritizationResponse.from_orm(prioritization)


@router.get("", response_model=PaginatedPrioritizations)
async def get_project_prioritizations(
    project_id: str,
    item_type: Optional[ItemType] = Query(None, description="Filter by item type"),
    priority_phase: Optional[PriorityPhase] = Query(None, description="Filter by priority phase"),
    min_score: Optional[int] = Query(None, ge=1, le=10, description="Minimum score filter"),
    max_score: Optional[int] = Query(None, ge=1, le=10, description="Maximum score filter"),
    assigned_by: Optional[str] = Query(None, description="Filter by assigned by user ID"),
    sort_by: Optional[str] = Query("priority_phase", description="Sort field"),
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prioritizations for a project with filtering and pagination"""
    
    filters = PrioritizationFilterParams(
        item_type=item_type,
        priority_phase=priority_phase,
        min_score=min_score,
        max_score=max_score,
        assigned_by=assigned_by,
        sort_by=sort_by or "priority_phase",
        sort_order=sort_order or "asc"
    )
    
    service = PrioritizationService(db)
    prioritizations, total = service.get_project_prioritizations(project_id, filters, skip, limit)
    
    return PaginatedPrioritizations(
        items=[PrioritizationResponse.from_orm(p) for p in prioritizations],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/board", response_model=PrioritizationBoard)
async def get_prioritization_board(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prioritization board organized by Now/Next/Later phases"""
    
    service = PrioritizationService(db)
    board_data = service.get_prioritization_board(project_id)
    
    # Convert dict responses to PrioritizationResponse objects
    def convert_items(items):
        result = []
        for item in items:
            if 'id' in item:  # These are actual prioritizations
                result.append(PrioritizationResponse.from_orm(type('obj', (), item)))
            else:  # These are unassigned items, create minimal response
                result.append(PrioritizationResponse(
                    id=item.get('item_id', ''),
                    project_id=project_id,
                    item_type=ItemType(item['item_type']),
                    item_id=item['item_id'],
                    priority_phase=PriorityPhase(item['priority_phase']),
                    score=None,
                    position=0,
                    notes=None,
                    assigned_by=None,
                    assigned_at=None,
                    updated_at=datetime.now(),
                    item_name=item.get('item_name', ''),
                    item_description=item.get('item_description', '')
                ))
        return result
    
    return PrioritizationBoard(
        now=convert_items(board_data['now']),
        next=convert_items(board_data['next']),
        later=convert_items(board_data['later']),
        unassigned=convert_items(board_data['unassigned'])
    )


@router.get("/stats", response_model=PrioritizationStats)
async def get_prioritization_stats(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prioritization statistics for a project"""
    
    service = PrioritizationService(db)
    stats = service.get_prioritization_stats(project_id)
    
    return PrioritizationStats(**stats)


@router.get("/{prioritization_id}", response_model=PrioritizationResponse)
async def get_prioritization(
    project_id: str,
    prioritization_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific prioritization by ID"""
    
    service = PrioritizationService(db)
    prioritization = service.get_prioritization(prioritization_id)
    
    if not prioritization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization not found"
        )
    
    # Verify prioritization belongs to the project
    if str(prioritization.project_id) != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization not found in this project"
        )
    
    return PrioritizationResponse.from_orm(prioritization)


@router.put("/{prioritization_id}", response_model=PrioritizationResponse)
async def update_prioritization(
    project_id: str,
    prioritization_id: str,
    update_data: PrioritizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a prioritization"""
    
    service = PrioritizationService(db)
    
    # Verify prioritization exists and belongs to project
    existing = service.get_prioritization(prioritization_id)
    if not existing or str(existing.project_id) != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization not found"
        )
    
    prioritization = service.update_prioritization(prioritization_id, update_data)
    
    if not prioritization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization not found"
        )
    
    return PrioritizationResponse.from_orm(prioritization)


@router.delete("/{prioritization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prioritization(
    project_id: str,
    prioritization_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a prioritization"""
    
    service = PrioritizationService(db)
    
    # Verify prioritization exists and belongs to project
    existing = service.get_prioritization(prioritization_id)
    if not existing or str(existing.project_id) != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization not found"
        )
    
    success = service.delete_prioritization(prioritization_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization not found"
        )


@router.post("/bulk-update", response_model=List[PrioritizationResponse])
async def bulk_update_prioritizations(
    project_id: str,
    bulk_update: BulkPrioritizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk update prioritizations (for drag-and-drop operations)"""
    
    service = PrioritizationService(db)
    prioritizations = service.bulk_update_prioritizations(project_id, bulk_update)
    
    return [PrioritizationResponse.from_orm(p) for p in prioritizations]


# Snapshot endpoints
@router.post("/snapshots", response_model=PrioritizationSnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_prioritization_snapshot(
    project_id: str,
    snapshot_data: PrioritizationSnapshotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a prioritization snapshot"""
    
    # Set project_id and created_by from context
    snapshot_data.project_id = project_id
    snapshot_data.created_by = str(current_user.id)
    
    service = PrioritizationService(db)
    snapshot = service.create_snapshot(snapshot_data)
    
    return PrioritizationSnapshotResponse.from_orm(snapshot)


@router.get("/snapshots", response_model=List[PrioritizationSnapshotResponse])
async def get_project_snapshots(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all prioritization snapshots for a project"""
    
    from app.models.prioritization import PrioritizationSnapshot
    
    snapshots = db.query(PrioritizationSnapshot).filter(
        PrioritizationSnapshot.project_id == project_id
    ).order_by(PrioritizationSnapshot.created_at.desc()).all()
    
    return [PrioritizationSnapshotResponse.from_orm(s) for s in snapshots]


@router.get("/snapshots/{snapshot_id}", response_model=PrioritizationSnapshotResponse)
async def get_prioritization_snapshot(
    project_id: str,
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific prioritization snapshot"""
    
    from app.models.prioritization import PrioritizationSnapshot
    
    snapshot = db.query(PrioritizationSnapshot).filter(
        PrioritizationSnapshot.id == snapshot_id,
        PrioritizationSnapshot.project_id == project_id
    ).first()
    
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization snapshot not found"
        )
    
    return PrioritizationSnapshotResponse.from_orm(snapshot)


@router.delete("/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prioritization_snapshot(
    project_id: str,
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a prioritization snapshot"""
    
    from app.models.prioritization import PrioritizationSnapshot
    
    snapshot = db.query(PrioritizationSnapshot).filter(
        PrioritizationSnapshot.id == snapshot_id,
        PrioritizationSnapshot.project_id == project_id
    ).first()
    
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization snapshot not found"
        )
    
    db.delete(snapshot)
    db.commit()
