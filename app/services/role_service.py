"""
Service for role management operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import joinedload, selectinload
import uuid

from app.models.role import Role, RoleStatus, DEFAULT_ROLES
from app.models.cta import CTA
from app.models.project import Project
from app.schemas.role import (
    RoleCreate, RoleUpdate, RoleSearchRequest, 
    RoleReorderRequest, RoleBulkCreateRequest
)
from app.core.exceptions import (
    NotFoundError, ValidationError, BusinessRuleError
)


class RoleService:
    """Service for role operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_role(
        self, 
        project_id: uuid.UUID, 
        role_data: RoleCreate, 
        user_id: uuid.UUID
    ) -> Role:
        """Create a new role."""
        # Validate project exists and user has access
        await self._validate_project_access(project_id, user_id)
        
        # Check for duplicate role names within project
        await self._validate_unique_name(project_id, role_data.name)
        
        # Handle template creation
        if role_data.template_type:
            template = self._get_template_by_type(role_data.template_type)
            if not template:
                raise ValidationError(f"Invalid template type: {role_data.template_type}")
            
            # Override with template values
            role_data.name = template['name']
            role_data.description = template['description']
            role_data.display_order = template['display_order']
        
        # Create role
        role = Role(
            project_id=project_id,
            name=role_data.name,
            description=role_data.description,
            display_order=role_data.display_order or 0,
            status=RoleStatus.ACTIVE,
            is_template=bool(role_data.template_type),
            template_type=role_data.template_type,
            created_by=user_id,
            updated_by=user_id
        )
        
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def get_role(self, role_id: uuid.UUID, user_id: uuid.UUID) -> Role:
        """Get a role by ID."""
        query = (
            select(Role)
            .options(selectinload(Role.ctas))
            .where(Role.id == role_id)
        )
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        
        if not role:
            raise NotFoundError(f"Role {role_id} not found")
        
        # Validate user has access to the project
        await self._validate_project_access(role.project_id, user_id)
        
        return role
    
    async def update_role(
        self, 
        role_id: uuid.UUID, 
        role_data: RoleUpdate, 
        user_id: uuid.UUID
    ) -> Role:
        """Update a role."""
        role = await self.get_role(role_id, user_id)
        
        # Check for name uniqueness if name is being updated
        if role_data.name and role_data.name != role.name:
            await self._validate_unique_name(role.project_id, role_data.name, role_id)
        
        # Update fields
        update_data = role_data.dict(exclude_unset=True)
        update_data['updated_by'] = user_id
        
        for field, value in update_data.items():
            setattr(role, field, value)
        
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def delete_role(self, role_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a role."""
        role = await self.get_role(role_id, user_id)
        
        # Check if role has CTAs
        cta_count = await self._get_role_cta_count(role_id)
        if cta_count > 0:
            raise BusinessRuleError(
                f"Cannot delete role '{role.name}' because it has {cta_count} CTAs. "
                "Please remove all CTAs first."
            )
        
        await self.db.delete(role)
        await self.db.commit()
        return True
    
    async def list_roles(
        self, 
        project_id: uuid.UUID, 
        user_id: uuid.UUID,
        search_params: Optional[RoleSearchRequest] = None
    ) -> tuple[List[Role], int]:
        """List roles for a project."""
        # Validate user has access
        await self._validate_project_access(project_id, user_id)
        
        # Build query
        query = (
            select(Role)
            .options(selectinload(Role.ctas))
            .where(Role.project_id == project_id)
        )
        
        # Apply filters
        if search_params:
            if search_params.name:
                query = query.where(Role.name.ilike(f"%{search_params.name}%"))
            if search_params.status:
                query = query.where(Role.status == search_params.status)
            if search_params.template_type:
                query = query.where(Role.template_type == search_params.template_type)
            if search_params.has_ctas is not None:
                if search_params.has_ctas:
                    query = query.where(Role.ctas.any())
                else:
                    query = query.where(~Role.ctas.any())
        
        # Apply sorting
        if search_params and search_params.sort_by:
            sort_field = getattr(Role, search_params.sort_by)
            if search_params.sort_order == "desc":
                sort_field = sort_field.desc()
            query = query.order_by(sort_field)
        else:
            query = query.order_by(Role.display_order, Role.name)
        
        # Execute query
        result = await self.db.execute(query)
        roles = result.scalars().all()
        
        # Get total count
        count_query = (
            select(func.count(Role.id))
            .where(Role.project_id == project_id)
        )
        if search_params:
            # Apply same filters to count query
            if search_params.name:
                count_query = count_query.where(Role.name.ilike(f"%{search_params.name}%"))
            if search_params.status:
                count_query = count_query.where(Role.status == search_params.status)
            if search_params.template_type:
                count_query = count_query.where(Role.template_type == search_params.template_type)
            if search_params.has_ctas is not None:
                if search_params.has_ctas:
                    count_query = count_query.where(Role.ctas.any())
                else:
                    count_query = count_query.where(~Role.ctas.any())
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(roles), total
    
    async def reorder_roles(
        self, 
        project_id: uuid.UUID, 
        reorder_data: RoleReorderRequest, 
        user_id: uuid.UUID
    ) -> List[Role]:
        """Reorder roles within a project."""
        # Validate user has access
        await self._validate_project_access(project_id, user_id)
        
        # Validate all roles belong to the project
        role_ids = [uuid.UUID(item['role_id']) for item in reorder_data.role_orders]
        query = select(Role).where(
            Role.id.in_(role_ids),
            Role.project_id == project_id
        )
        result = await self.db.execute(query)
        existing_roles = {role.id: role for role in result.scalars().all()}
        
        if len(existing_roles) != len(role_ids):
            raise ValidationError("Some roles not found or don't belong to the project")
        
        # Update display orders
        for item in reorder_data.role_orders:
            role_id = uuid.UUID(item['role_id'])
            role = existing_roles[role_id]
            role.display_order = item['display_order']
            role.updated_by = user_id
        
        await self.db.commit()
        
        # Return updated roles in order
        return list(existing_roles.values())
    
    async def create_default_roles(
        self, 
        project_id: uuid.UUID, 
        template_types: List[str], 
        user_id: uuid.UUID
    ) -> tuple[List[Role], List[Dict[str, Any]]]:
        """Create default roles from templates."""
        # Validate user has access
        await self._validate_project_access(project_id, user_id)
        
        created_roles = []
        skipped_roles = []
        
        for template_type in template_types:
            template = self._get_template_by_type(template_type)
            if not template:
                skipped_roles.append({
                    'template_type': template_type,
                    'reason': 'Invalid template type'
                })
                continue
            
            # Check if role with this name already exists
            existing = await self._check_role_exists(project_id, template['name'])
            if existing:
                skipped_roles.append({
                    'template_type': template_type,
                    'name': template['name'],
                    'reason': 'Role with this name already exists'
                })
                continue
            
            # Create role
            role = Role(
                project_id=project_id,
                name=template['name'],
                description=template['description'],
                display_order=template['display_order'],
                status=RoleStatus.ACTIVE,
                is_template=True,
                template_type=template_type,
                created_by=user_id,
                updated_by=user_id
            )
            
            self.db.add(role)
            created_roles.append(role)
        
        if created_roles:
            await self.db.commit()
            for role in created_roles:
                await self.db.refresh(role)
        
        return created_roles, skipped_roles
    
    async def get_default_templates(self) -> List[Dict[str, Any]]:
        """Get available default role templates."""
        return [
            {
                'name': template['name'],
                'description': template['description'],
                'template_type': template_type,
                'display_order': template['display_order']
            }
            for template_type, template in DEFAULT_ROLES.items()
        ]
    
    async def get_role_stats(
        self, 
        project_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get role statistics for a project."""
        # Validate user has access
        await self._validate_project_access(project_id, user_id)
        
        # Get basic role count
        role_count_query = (
            select(func.count(Role.id))
            .where(Role.project_id == project_id)
        )
        role_count_result = await self.db.execute(role_count_query)
        total_roles = role_count_result.scalar()
        
        # Get status breakdown
        status_query = (
            select(Role.status, func.count(Role.id))
            .where(Role.project_id == project_id)
            .group_by(Role.status)
        )
        status_result = await self.db.execute(status_query)
        status_breakdown = {status: count for status, count in status_result.all()}
        
        # Get template breakdown
        template_query = (
            select(Role.template_type, func.count(Role.id))
            .where(Role.project_id == project_id, Role.template_type.isnot(None))
            .group_by(Role.template_type)
        )
        template_result = await self.db.execute(template_query)
        template_breakdown = {template_type: count for template_type, count in template_result.all()}
        
        # Get roles with CTAs
        roles_with_ctas_query = (
            select(func.count(func.distinct(Role.id)))
            .join(CTA, Role.id == CTA.role_id)
            .where(Role.project_id == project_id)
        )
        roles_with_ctas_result = await self.db.execute(roles_with_ctas_query)
        roles_with_ctas = roles_with_ctas_result.scalar() or 0
        
        return {
            'project_id': project_id,
            'total_roles': total_roles,
            'status_breakdown': status_breakdown,
            'template_breakdown': template_breakdown,
            'roles_with_ctas': roles_with_ctas,
            'roles_without_ctas': total_roles - roles_with_ctas
        }
    
    # Private helper methods
    
    async def _validate_project_access(self, project_id: uuid.UUID, user_id: uuid.UUID):
        """Validate user has access to the project."""
        query = select(Project).where(Project.id == project_id)
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()
        
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        # For now, we'll skip detailed permission checking
        # In a real implementation, you'd check project membership
    
    async def _validate_unique_name(
        self, 
        project_id: uuid.UUID, 
        name: str, 
        exclude_id: Optional[uuid.UUID] = None
    ):
        """Validate role name is unique within project."""
        query = (
            select(Role)
            .where(Role.project_id == project_id, Role.name == name)
        )
        
        if exclude_id:
            query = query.where(Role.id != exclude_id)
        
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValidationError(f"Role name '{name}' already exists in this project")
    
    async def _check_role_exists(self, project_id: uuid.UUID, name: str) -> bool:
        """Check if a role with the given name exists in the project."""
        query = (
            select(Role)
            .where(Role.project_id == project_id, Role.name == name)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _get_role_cta_count(self, role_id: uuid.UUID) -> int:
        """Get count of CTAs for a role."""
        query = select(func.count(CTA.id)).where(CTA.role_id == role_id)
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    def _get_template_by_type(self, template_type: str) -> Optional[Dict[str, Any]]:
        """Get a default role template by type."""
        return DEFAULT_ROLES.get(template_type)
