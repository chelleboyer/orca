"""
API routes for role management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.services.role_service import RoleService
from app.schemas.role import (
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse,
    RoleReorderRequest, RoleBulkCreateRequest, RoleBulkCreateResponse,
    RoleSearchRequest, RoleSearchResponse, DefaultRolesResponse
)
from app.core.exceptions import NotFoundError, ValidationError, BusinessRuleError

router = APIRouter()


@router.post("/projects/{project_id}/roles", response_model=RoleResponse)
async def create_role(
    project_id: uuid.UUID,
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new role for a project."""
    try:
        role_service = RoleService(db)
        role = await role_service.create_role(project_id, role_data, current_user.id)
        
        # Convert to response format
        return RoleResponse(
            id=role.id,
            project_id=role.project_id,
            name=role.name,
            description=role.description,
            status=role.status.value,
            display_order=role.display_order,
            is_template=role.is_template,
            template_type=role.template_type,
            created_at=role.created_at,
            updated_at=role.updated_at,
            created_by=role.created_by,
            updated_by=role.updated_by,
            cta_count=len(role.ctas) if role.ctas else 0,
            can_be_deleted=len(role.ctas) == 0 if role.ctas else True
        )
    except (NotFoundError, ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/projects/{project_id}/roles", response_model=RoleListResponse)
async def list_roles(
    project_id: uuid.UUID,
    name: Optional[str] = Query(None, description="Filter by role name"),
    status: Optional[str] = Query(None, description="Filter by role status"),
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    has_ctas: Optional[bool] = Query(None, description="Filter by CTA presence"),
    sort_by: Optional[str] = Query("display_order", description="Sort field"),
    sort_order: Optional[str] = Query("asc", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List roles for a project."""
    try:
        # Build search parameters
        search_params = RoleSearchRequest(
            name=name,
            status=status,
            template_type=template_type,
            has_ctas=has_ctas,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        role_service = RoleService(db)
        roles, total = await role_service.list_roles(project_id, current_user.id, search_params)
        
        # Convert to response format
        role_responses = []
        for role in roles:
            role_responses.append(RoleResponse(
                id=role.id,
                project_id=role.project_id,
                name=role.name,
                description=role.description,
                status=role.status.value,
                display_order=role.display_order,
                is_template=role.is_template,
                template_type=role.template_type,
                created_at=role.created_at,
                updated_at=role.updated_at,
                created_by=role.created_by,
                updated_by=role.updated_by,
                cta_count=len(role.ctas) if role.ctas else 0,
                can_be_deleted=len(role.ctas) == 0 if role.ctas else True
            ))
        
        return RoleListResponse(
            roles=role_responses,
            total=total,
            project_id=project_id
        )
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/projects/{project_id}/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    project_id: uuid.UUID,
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific role."""
    try:
        role_service = RoleService(db)
        role = await role_service.get_role(role_id, current_user.id)
        
        return RoleResponse(
            id=role.id,
            project_id=role.project_id,
            name=role.name,
            description=role.description,
            status=role.status.value,
            display_order=role.display_order,
            is_template=role.is_template,
            template_type=role.template_type,
            created_at=role.created_at,
            updated_at=role.updated_at,
            created_by=role.created_by,
            updated_by=role.updated_by,
            cta_count=len(role.ctas) if role.ctas else 0,
            can_be_deleted=len(role.ctas) == 0 if role.ctas else True
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/projects/{project_id}/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    project_id: uuid.UUID,
    role_id: uuid.UUID,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a role."""
    try:
        role_service = RoleService(db)
        role = await role_service.update_role(role_id, role_data, current_user.id)
        
        return RoleResponse(
            id=role.id,
            project_id=role.project_id,
            name=role.name,
            description=role.description,
            status=role.status.value,
            display_order=role.display_order,
            is_template=role.is_template,
            template_type=role.template_type,
            created_at=role.created_at,
            updated_at=role.updated_at,
            created_by=role.created_by,
            updated_by=role.updated_by,
            cta_count=len(role.ctas) if role.ctas else 0,
            can_be_deleted=len(role.ctas) == 0 if role.ctas else True
        )
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/projects/{project_id}/roles/{role_id}")
async def delete_role(
    project_id: uuid.UUID,
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a role."""
    try:
        role_service = RoleService(db)
        await role_service.delete_role(role_id, current_user.id)
        return {"message": "Role deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/projects/{project_id}/roles/reorder")
async def reorder_roles(
    project_id: uuid.UUID,
    reorder_data: RoleReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder roles within a project."""
    try:
        role_service = RoleService(db)
        await role_service.reorder_roles(project_id, reorder_data, current_user.id)
        return {"message": "Roles reordered successfully"}
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/role-templates", response_model=DefaultRolesResponse)
async def get_default_role_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available default role templates."""
    role_service = RoleService(db)
    templates = await role_service.get_default_templates()
    return DefaultRolesResponse(templates=templates)


@router.post("/projects/{project_id}/roles/bulk-create", response_model=RoleBulkCreateResponse)
async def create_default_roles(
    project_id: uuid.UUID,
    bulk_data: RoleBulkCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple roles from default templates."""
    try:
        role_service = RoleService(db)
        created_roles, skipped_roles = await role_service.create_default_roles(
            project_id, bulk_data.template_types, current_user.id
        )
        
        # Convert to response format
        created_responses = []
        for role in created_roles:
            created_responses.append(RoleResponse(
                id=role.id,
                project_id=role.project_id,
                name=role.name,
                description=role.description,
                status=role.status.value,
                display_order=role.display_order,
                is_template=role.is_template,
                template_type=role.template_type,
                created_at=role.created_at,
                updated_at=role.updated_at,
                created_by=role.created_by,
                updated_by=role.updated_by,
                cta_count=0,  # New roles have no CTAs
                can_be_deleted=True
            ))
        
        return RoleBulkCreateResponse(
            created_roles=created_responses,
            skipped_roles=skipped_roles,
            total_created=len(created_roles),
            total_skipped=len(skipped_roles)
        )
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/projects/{project_id}/roles/stats")
async def get_role_stats(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get role statistics for a project."""
    try:
        role_service = RoleService(db)
        stats = await role_service.get_role_stats(project_id, current_user.id)
        return stats
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
