"""
API endpoints for attribute management
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.attribute import AttributeType
from app.services.attribute_service import AttributeService
from app.schemas.attribute import (
    AttributeCreate, AttributeUpdate, AttributeResponse, AttributeListResponse,
    AttributeFilterParams, AttributeStatsResponse,
    ObjectAttributeCreate, ObjectAttributeUpdate, ObjectAttributeResponse,
    BulkAttributeCreate, BulkAttributeUpdate
)

router = APIRouter()


@router.post("/projects/{project_id}/attributes", response_model=AttributeResponse, status_code=status.HTTP_201_CREATED)
def create_attribute(
    project_id: uuid.UUID,
    attribute_data: AttributeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new attribute for a project"""
    service = AttributeService(db)
    
    # Ensure project_id matches the one in the request body
    attribute_data.project_id = project_id
    
    try:
        attribute = service.create_attribute(attribute_data)
        return AttributeResponse.model_validate(attribute)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attribute: {str(e)}"
        )


@router.get("/projects/{project_id}/attributes", response_model=AttributeListResponse)
def list_attributes(
    project_id: uuid.UUID,
    name: Optional[str] = Query(None, description="Filter by attribute name"),
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    is_core: Optional[bool] = Query(None, description="Filter by core status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    reference_object_id: Optional[uuid.UUID] = Query(None, description="Filter by referenced object"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get filtered list of attributes for a project"""
    # Convert string data_type to enum if provided
    parsed_data_type = None
    if data_type:
        try:
            parsed_data_type = AttributeType(data_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid data_type. Must be one of: {[e.value for e in AttributeType]}"
            )
    
    filters = AttributeFilterParams(
        name=name,
        data_type=parsed_data_type,
        is_core=is_core,
        is_active=is_active,
        reference_object_id=reference_object_id,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    service = AttributeService(db)
    attributes, total = service.get_attributes(filters, project_id)
    
    # Calculate pagination metadata
    has_next = page * per_page < total
    has_prev = page > 1
    
    return AttributeListResponse(
        attributes=[AttributeResponse.model_validate(attr) for attr in attributes],
        total=total,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=has_prev
    )


@router.get("/projects/{project_id}/attributes/stats", response_model=AttributeStatsResponse)
def get_attribute_stats(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attribute statistics for a project"""
    service = AttributeService(db)
    stats = service.get_attribute_stats(project_id)
    
    return AttributeStatsResponse(**stats)


@router.get("/projects/{project_id}/attributes/{attribute_id}", response_model=AttributeResponse)
def get_attribute(
    project_id: uuid.UUID,
    attribute_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific attribute by ID"""
    service = AttributeService(db)
    attribute = service.get_attribute(attribute_id, project_id)
    
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found"
        )
    
    return AttributeResponse.model_validate(attribute)


@router.put("/projects/{project_id}/attributes/{attribute_id}", response_model=AttributeResponse)
def update_attribute(
    project_id: uuid.UUID,
    attribute_id: uuid.UUID,
    update_data: AttributeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing attribute"""
    service = AttributeService(db)
    
    try:
        attribute = service.update_attribute(attribute_id, project_id, update_data)
        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute not found"
            )
        
        return AttributeResponse.model_validate(attribute)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update attribute: {str(e)}"
        )


@router.delete("/projects/{project_id}/attributes/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attribute(
    project_id: uuid.UUID,
    attribute_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (soft delete) an attribute"""
    service = AttributeService(db)
    
    success = service.delete_attribute(attribute_id, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found"
        )


@router.post("/projects/{project_id}/attributes/bulk", response_model=List[AttributeResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_attributes(
    project_id: uuid.UUID,
    bulk_data: BulkAttributeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple attributes in bulk"""
    service = AttributeService(db)
    
    # Ensure all attributes have the correct project_id
    for attr_data in bulk_data.attributes:
        attr_data.project_id = project_id
    
    try:
        attributes = service.bulk_create_attributes(bulk_data.attributes)
        return [AttributeResponse.model_validate(attr) for attr in attributes]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attributes: {str(e)}"
        )


# Object Attribute Value endpoints
@router.post("/projects/{project_id}/attributes/values", response_model=ObjectAttributeResponse, status_code=status.HTTP_201_CREATED)
def set_object_attribute_value(
    project_id: uuid.UUID,
    obj_attr_data: ObjectAttributeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set or update an object's attribute value"""
    service = AttributeService(db)
    
    try:
        obj_attr = service.set_object_attribute_value(obj_attr_data)
        return ObjectAttributeResponse.model_validate(obj_attr)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set attribute value: {str(e)}"
        )


@router.get("/projects/{project_id}/attributes/values/{object_id}", response_model=List[ObjectAttributeResponse])
def get_object_attribute_values(
    project_id: uuid.UUID,
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all attribute values for a specific object"""
    service = AttributeService(db)
    
    obj_attributes = service.get_object_attributes(object_id)
    return [ObjectAttributeResponse.model_validate(obj_attr) for obj_attr in obj_attributes]


@router.delete("/projects/{project_id}/attributes/values/{object_id}/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_object_attribute_value(
    project_id: uuid.UUID,
    object_id: uuid.UUID,
    attribute_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove an object's attribute value"""
    service = AttributeService(db)
    
    success = service.remove_object_attribute(object_id, attribute_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object attribute not found"
        )


@router.put("/projects/{project_id}/attributes/values/bulk", response_model=List[ObjectAttributeResponse])
def bulk_update_object_attribute_values(
    project_id: uuid.UUID,
    bulk_data: BulkAttributeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update object attribute values"""
    service = AttributeService(db)
    
    try:
        obj_attributes = service.bulk_update_object_attributes(bulk_data.updates)
        return [ObjectAttributeResponse.model_validate(obj_attr) for obj_attr in obj_attributes]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update attribute values: {str(e)}"
        )
