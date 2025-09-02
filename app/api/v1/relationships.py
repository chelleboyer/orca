"""
API routes for relationship management.
Handles OOUX relationship CRUD operations and NOM matrix functionality.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.core.security import get_current_user_from_token
from app.models.user import User
from app.services.relationship_service import RelationshipService
from app.schemas.relationship import (
    RelationshipCreate, RelationshipUpdate, RelationshipResponse,
    RelationshipSearchRequest, RelationshipSearchResponse,
    NOMMatrixResponse, RelationshipLockRequest, RelationshipLockResponse,
    PresenceUpdateRequest, PresenceResponse
)
from app.core.exceptions import ValidationError, ConflictError

router = APIRouter(prefix="/projects/{project_id}/relationships", tags=["relationships"])


async def get_current_user(credentials: dict = Depends(get_current_user_from_token), db: Session = Depends(get_db)) -> User:
    """Dependency to get current user from token."""
    user_id = credentials.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RelationshipResponse)
async def create_relationship(
    project_id: str,
    relationship_data: RelationshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new relationship between objects in a project.
    
    Args:
        project_id: UUID of the project
        relationship_data: Relationship creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created relationship data
        
    Raises:
        409: If relationship already exists
        400: If validation fails
    """
    try:
        service = RelationshipService(db)
        relationship = service.create_relationship(project_id, relationship_data, str(current_user.id))
        return RelationshipResponse.from_orm(relationship)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship(
    project_id: str,
    relationship_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific relationship by ID.
    
    Args:
        project_id: UUID of the project
        relationship_id: UUID of the relationship
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Relationship data
        
    Raises:
        404: If relationship not found
    """
    service = RelationshipService(db)
    relationship = service.get_relationship(relationship_id, project_id)
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    return RelationshipResponse.from_orm(relationship)


@router.put("/{relationship_id}", response_model=RelationshipResponse)
async def update_relationship(
    project_id: str,
    relationship_id: str,
    relationship_data: RelationshipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing relationship.
    
    Args:
        project_id: UUID of the project
        relationship_id: UUID of the relationship
        relationship_data: Relationship update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated relationship data
        
    Raises:
        404: If relationship not found
        400: If validation fails
    """
    try:
        service = RelationshipService(db)
        relationship = service.update_relationship(relationship_id, project_id, relationship_data, str(current_user.id))
        
        if not relationship:
            raise HTTPException(status_code=404, detail="Relationship not found")
        
        return RelationshipResponse.from_orm(relationship)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    project_id: str,
    relationship_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a relationship.
    
    Args:
        project_id: UUID of the project
        relationship_id: UUID of the relationship
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        404: If relationship not found
        400: If deletion fails
    """
    try:
        service = RelationshipService(db)
        deleted = service.delete_relationship(relationship_id, project_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Relationship not found")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search", response_model=RelationshipSearchResponse)
async def search_relationships(
    project_id: str,
    search_request: RelationshipSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search and filter relationships within a project.
    
    Args:
        project_id: UUID of the project
        search_request: Search parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Search results with pagination info
    """
    service = RelationshipService(db)
    relationships, total = service.search_relationships(project_id, search_request)
    
    offset = search_request.offset or 0
    limit = search_request.limit or 50
    has_more = (offset + limit) < total
    
    return RelationshipSearchResponse(
        relationships=[RelationshipResponse.from_orm(rel) for rel in relationships],
        total=total,
        offset=offset,
        limit=limit,
        has_more=has_more
    )


@router.get("/", response_model=List[RelationshipResponse])
async def list_relationships(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all relationships for a project.
    
    Args:
        project_id: UUID of the project
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of all relationships in the project
    """
    service = RelationshipService(db)
    relationships = service.get_project_relationships(project_id)
    
    return [RelationshipResponse.from_orm(rel) for rel in relationships]


# NOM Matrix endpoints

@router.get("/matrix/nom", response_model=NOMMatrixResponse)
async def get_nom_matrix(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the complete Nested Object Matrix (NOM) for a project.
    
    Args:
        project_id: UUID of the project
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Complete matrix data with objects and relationships
    """
    service = RelationshipService(db)
    matrix_data = service.get_nom_matrix(project_id)
    
    return matrix_data


# Collaborative editing endpoints

@router.post("/locks", response_model=RelationshipLockResponse)
async def acquire_lock(
    project_id: str,
    lock_request: RelationshipLockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Acquire a lock on a relationship for editing.
    
    Args:
        project_id: UUID of the project
        lock_request: Lock request data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Lock information if successful
        
    Raises:
        409: If already locked by another user
    """
    service = RelationshipService(db)
    lock = service.acquire_lock(project_id, lock_request, str(current_user.id))
    
    if not lock:
        raise HTTPException(status_code=409, detail="Already locked by another user")
    
    return RelationshipLockResponse.from_orm(lock)


@router.delete("/locks/{lock_id}", status_code=status.HTTP_204_NO_CONTENT)
async def release_lock(
    project_id: str,
    lock_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Release a relationship lock.
    
    Args:
        project_id: UUID of the project
        lock_id: UUID of the lock
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        404: If lock not found or not owned by user
    """
    service = RelationshipService(db)
    released = service.release_lock(lock_id, str(current_user.id))
    
    if not released:
        raise HTTPException(status_code=404, detail="Lock not found or not owned by user")


@router.post("/presence", response_model=PresenceResponse)
async def update_presence(
    project_id: str,
    presence_data: PresenceUpdateRequest,
    session_id: str = Query(..., description="Session identifier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user presence in the project.
    
    Args:
        project_id: UUID of the project
        presence_data: Presence update data
        session_id: Session identifier
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated presence information
    """
    service = RelationshipService(db)
    presence = service.update_presence(project_id, str(current_user.id), session_id, presence_data)
    
    return PresenceResponse.from_orm(presence)


@router.get("/presence", response_model=List[PresenceResponse])
async def get_active_presence(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all active user presence in the project.
    
    Args:
        project_id: UUID of the project
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of active presence records
    """
    service = RelationshipService(db)
    presence_list = service.get_active_presence(project_id)
    
    return [PresenceResponse.from_orm(presence) for presence in presence_list]


# Utility endpoints

@router.post("/maintenance/cleanup-locks")
async def cleanup_expired_locks(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up expired relationship locks.
    
    Args:
        project_id: UUID of the project
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Number of locks cleaned up
    """
    service = RelationshipService(db)
    cleaned_count = service.cleanup_expired_locks()
    
    return {"cleaned_locks": cleaned_count}


@router.post("/maintenance/cleanup-presence")
async def cleanup_inactive_presence(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up inactive presence records.
    
    Args:
        project_id: UUID of the project
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Number of presence records cleaned up
    """
    service = RelationshipService(db)
    cleaned_count = service.cleanup_inactive_presence()
    
    return {"cleaned_presence": cleaned_count}
