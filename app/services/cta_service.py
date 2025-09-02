"""
Service for CTA (Call-to-Action) management operations.
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.orm import joinedload, selectinload
import uuid
from datetime import datetime

from app.models.cta import CTA, CRUDType, CTAStatus
from app.models.role import Role
from app.models.object import Object
from app.models.project import Project
from app.schemas.cta import (
    CTACreate, CTAUpdate, CTASearchRequest, 
    CTABulkCreateRequest, UserStoryGenerateRequest,
    CTAExportRequest
)
from app.core.exceptions import (
    NotFoundError, ValidationError, BusinessRuleError
)


class CTAService:
    """Service for CTA operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_cta(
        self, 
        project_id: uuid.UUID, 
        cta_data: CTACreate, 
        user_id: uuid.UUID
    ) -> CTA:
        """Create a new CTA."""
        # Validate project, role, and object exist and belong to project
        await self._validate_cta_relationships(project_id, cta_data.role_id, cta_data.object_id, user_id)
        
        # Check for duplicate CTA (same role, object, CRUD type)
        await self._validate_unique_cta(project_id, cta_data.role_id, cta_data.object_id, cta_data.crud_type)
        
        # Create CTA
        cta = CTA(
            project_id=project_id,
            role_id=cta_data.role_id,
            object_id=cta_data.object_id,
            crud_type=cta_data.crud_type,
            description=cta_data.description,
            preconditions=cta_data.preconditions,
            postconditions=cta_data.postconditions,
            acceptance_criteria=cta_data.acceptance_criteria,
            business_value=cta_data.business_value,
            priority=cta_data.priority or 1,
            story_points=cta_data.story_points,
            status=CTAStatus.DRAFT,
            created_by=user_id,
            updated_by=user_id
        )
        
        self.db.add(cta)
        await self.db.commit()
        await self.db.refresh(cta)
        return cta
    
    async def get_cta(self, cta_id: uuid.UUID, user_id: uuid.UUID) -> CTA:
        """Get a CTA by ID."""
        query = (
            select(CTA)
            .options(
                joinedload(CTA.role),
                joinedload(CTA.object)
            )
            .where(CTA.id == cta_id)
        )
        result = await self.db.execute(query)
        cta = result.scalar_one_or_none()
        
        if not cta:
            raise NotFoundError(f"CTA {cta_id} not found")
        
        # Validate user has access to the project
        await self._validate_project_access(cta.project_id, user_id)
        
        return cta
    
    async def update_cta(
        self, 
        cta_id: uuid.UUID, 
        cta_data: CTAUpdate, 
        user_id: uuid.UUID
    ) -> CTA:
        """Update a CTA."""
        cta = await self.get_cta(cta_id, user_id)
        
        # Check for CRUD type uniqueness if being updated
        if cta_data.crud_type and cta_data.crud_type != cta.crud_type:
            await self._validate_unique_cta(
                cta.project_id, cta.role_id, cta.object_id, cta_data.crud_type, cta_id
            )
        
        # Update fields
        update_data = cta_data.dict(exclude_unset=True)
        update_data['updated_by'] = user_id
        
        for field, value in update_data.items():
            setattr(cta, field, value)
        
        await self.db.commit()
        await self.db.refresh(cta)
        return cta
    
    async def delete_cta(self, cta_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a CTA."""
        cta = await self.get_cta(cta_id, user_id)
        
        await self.db.delete(cta)
        await self.db.commit()
        return True
    
    async def list_ctas(
        self, 
        project_id: uuid.UUID, 
        user_id: uuid.UUID,
        search_params: Optional[CTASearchRequest] = None
    ) -> Tuple[List[CTA], int]:
        """List CTAs for a project."""
        # Validate user has access
        await self._validate_project_access(project_id, user_id)
        
        # Build query
        query = (
            select(CTA)
            .options(
                joinedload(CTA.role),
                joinedload(CTA.object)
            )
            .where(CTA.project_id == project_id)
        )
        
        # Apply filters
        if search_params:
            if search_params.role_id:
                query = query.where(CTA.role_id == search_params.role_id)
            if search_params.object_id:
                query = query.where(CTA.object_id == search_params.object_id)
            if search_params.crud_type:
                query = query.where(CTA.crud_type == search_params.crud_type)
            if search_params.status:
                query = query.where(CTA.status == search_params.status)
            if search_params.priority:
                query = query.where(CTA.priority == search_params.priority)
            if search_params.has_business_rules is not None:
                if search_params.has_business_rules:
                    query = query.where(
                        or_(
                            CTA.preconditions.isnot(None),
                            CTA.postconditions.isnot(None)
                        )
                    )
                else:
                    query = query.where(
                        and_(
                            CTA.preconditions.is_(None),
                            CTA.postconditions.is_(None)
                        )
                    )
            if search_params.search_text:
                search_text = f"%{search_params.search_text}%"
                query = query.where(
                    or_(
                        CTA.description.ilike(search_text),
                        CTA.preconditions.ilike(search_text),
                        CTA.postconditions.ilike(search_text),
                        CTA.acceptance_criteria.ilike(search_text),
                        CTA.business_value.ilike(search_text)
                    )
                )
        
        # Apply sorting
        if search_params and search_params.sort_by:
            sort_field = getattr(CTA, search_params.sort_by)
            if search_params.sort_order == "desc":
                sort_field = sort_field.desc()
            query = query.order_by(sort_field)
        else:
            query = query.order_by(CTA.priority.desc(), CTA.created_at)
        
        # Execute query
        result = await self.db.execute(query)
        ctas = result.scalars().all()
        
        # Get total count with same filters
        count_query = (
            select(func.count(CTA.id))
            .where(CTA.project_id == project_id)
        )
        
        if search_params:
            # Apply same filters to count query
            if search_params.role_id:
                count_query = count_query.where(CTA.role_id == search_params.role_id)
            if search_params.object_id:
                count_query = count_query.where(CTA.object_id == search_params.object_id)
            if search_params.crud_type:
                count_query = count_query.where(CTA.crud_type == search_params.crud_type)
            if search_params.status:
                count_query = count_query.where(CTA.status == search_params.status)
            if search_params.priority:
                count_query = count_query.where(CTA.priority == search_params.priority)
            if search_params.search_text:
                search_text = f"%{search_params.search_text}%"
                count_query = count_query.where(
                    or_(
                        CTA.description.ilike(search_text),
                        CTA.preconditions.ilike(search_text),
                        CTA.postconditions.ilike(search_text),
                        CTA.acceptance_criteria.ilike(search_text),
                        CTA.business_value.ilike(search_text)
                    )
                )
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(ctas), total
    
    async def get_cta_matrix(
        self, 
        project_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get CTA matrix data for a project."""
        # Validate user has access
        await self._validate_project_access(project_id, user_id)
        
        # Get all roles for the project
        roles_query = (
            select(Role)
            .where(Role.project_id == project_id)
            .order_by(Role.display_order, Role.name)
        )
        roles_result = await self.db.execute(roles_query)
        roles = list(roles_result.scalars().all())
        
        # Get all objects for the project
        objects_query = (
            select(Object)
            .where(Object.project_id == project_id)
            .order_by(Object.display_order, Object.name)
        )
        objects_result = await self.db.execute(objects_query)
        objects = list(objects_result.scalars().all())
        
        # Get all CTAs for the project
        ctas_query = (
            select(CTA)
            .options(
                joinedload(CTA.role),
                joinedload(CTA.object)
            )
            .where(CTA.project_id == project_id)
        )
        ctas_result = await self.db.execute(ctas_query)
        all_ctas = list(ctas_result.scalars().all())
        
        # Organize CTAs by role and object
        cta_matrix = {}
        crud_summary = {"CREATE": 0, "READ": 0, "UPDATE": 0, "DELETE": 0}
        
        for cta in all_ctas:
            key = (cta.role_id, cta.object_id)
            if key not in cta_matrix:
                cta_matrix[key] = {
                    'ctas': [],
                    'has_create': False,
                    'has_read': False,
                    'has_update': False,
                    'has_delete': False
                }
            
            cta_matrix[key]['ctas'].append(cta)
            cta_matrix[key][f'has_{cta.crud_type.lower()}'] = True
            crud_summary[cta.crud_type] += 1
        
        # Build matrix rows
        matrix_rows = []
        for role in roles:
            cells = []
            role_cta_count = 0
            
            for obj in objects:
                key = (role.id, obj.id)
                cell_data = cta_matrix.get(key, {
                    'ctas': [],
                    'has_create': False,
                    'has_read': False,
                    'has_update': False,
                    'has_delete': False
                })
                
                cell = {
                    'role_id': role.id,
                    'object_id': obj.id,
                    'role_name': role.name,
                    'object_name': obj.name,
                    'ctas': cell_data['ctas'],
                    'has_create': cell_data['has_create'],
                    'has_read': cell_data['has_read'],
                    'has_update': cell_data['has_update'],
                    'has_delete': cell_data['has_delete'],
                    'total_ctas': len(cell_data['ctas'])
                }
                
                cells.append(cell)
                role_cta_count += len(cell_data['ctas'])
            
            matrix_rows.append({
                'role_id': role.id,
                'role_name': role.name,
                'cells': cells,
                'total_ctas': role_cta_count
            })
        
        return {
            'project_id': project_id,
            'roles': [{'id': r.id, 'name': r.name} for r in roles],
            'objects': [{'id': o.id, 'name': o.name} for o in objects],
            'rows': matrix_rows,
            'total_ctas': len(all_ctas),
            'crud_summary': crud_summary
        }
    
    async def bulk_create_ctas(
        self, 
        project_id: uuid.UUID, 
        bulk_data: CTABulkCreateRequest, 
        user_id: uuid.UUID
    ) -> Tuple[List[CTA], List[Dict[str, Any]]]:
        """Create multiple CTAs in bulk."""
        # Validate user has access
        await self._validate_project_access(project_id, user_id)
        
        created_ctas = []
        failed_ctas = []
        
        for cta_data in bulk_data.ctas:
            try:
                # Validate relationships
                await self._validate_cta_relationships(
                    project_id, cta_data.role_id, cta_data.object_id, user_id
                )
                
                # Check for duplicates
                await self._validate_unique_cta(
                    project_id, cta_data.role_id, cta_data.object_id, cta_data.crud_type
                )
                
                # Create CTA
                cta = CTA(
                    project_id=project_id,
                    role_id=cta_data.role_id,
                    object_id=cta_data.object_id,
                    crud_type=cta_data.crud_type,
                    description=cta_data.description,
                    preconditions=cta_data.preconditions,
                    postconditions=cta_data.postconditions,
                    acceptance_criteria=cta_data.acceptance_criteria,
                    business_value=cta_data.business_value,
                    priority=cta_data.priority or 1,
                    story_points=cta_data.story_points,
                    status=CTAStatus.DRAFT,
                    created_by=user_id,
                    updated_by=user_id
                )
                
                self.db.add(cta)
                created_ctas.append(cta)
                
            except Exception as e:
                failed_ctas.append({
                    'cta_data': cta_data.dict(),
                    'error': str(e)
                })
        
        if created_ctas:
            await self.db.commit()
            for cta in created_ctas:
                await self.db.refresh(cta)
        
        return created_ctas, failed_ctas
    
    async def generate_user_story(
        self, 
        cta_id: uuid.UUID, 
        user_id: uuid.UUID,
        story_request: UserStoryGenerateRequest
    ) -> str:
        """Generate a user story for a CTA."""
        cta = await self.get_cta(cta_id, user_id)
        
        # Load related entities
        await self.db.refresh(cta, ['role', 'object'])
        
        # Generate user story based on template
        role_name = cta.role.name
        object_name = cta.object.name
        crud_action = self._get_crud_action_text(cta.crud_type)
        
        if story_request.template_type == "standard":
            story = f"As a {role_name}, I want to {crud_action} {object_name} so that {cta.business_value or 'I can accomplish my goals'}."
        else:
            # Default format
            story = f"As a {role_name}, I want to {crud_action} {object_name}."
        
        if cta.description:
            story += f"\n\nDescription: {cta.description}"
        
        if story_request.include_acceptance_criteria and cta.acceptance_criteria:
            story += f"\n\nAcceptance Criteria:\n{cta.acceptance_criteria}"
        
        if story_request.include_business_rules:
            if cta.preconditions:
                story += f"\n\nPreconditions:\n{cta.preconditions}"
            if cta.postconditions:
                story += f"\n\nPostconditions:\n{cta.postconditions}"
        
        # Update CTA with generated story
        cta.user_story = story
        cta.updated_by = user_id
        await self.db.commit()
        
        return story
    
    async def get_cta_stats(
        self, 
        project_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get CTA statistics for a project."""
        # Validate user has access
        await self._validate_project_access(project_id, user_id)
        
        # Get basic CTA count
        cta_count_query = (
            select(func.count(CTA.id))
            .where(CTA.project_id == project_id)
        )
        cta_count_result = await self.db.execute(cta_count_query)
        total_ctas = cta_count_result.scalar()
        
        # CRUD breakdown
        crud_query = (
            select(CTA.crud_type, func.count(CTA.id))
            .where(CTA.project_id == project_id)
            .group_by(CTA.crud_type)
        )
        crud_result = await self.db.execute(crud_query)
        crud_breakdown = {crud_type: count for crud_type, count in crud_result.all()}
        
        # Status breakdown
        status_query = (
            select(CTA.status, func.count(CTA.id))
            .where(CTA.project_id == project_id)
            .group_by(CTA.status)
        )
        status_result = await self.db.execute(status_query)
        status_breakdown = {status: count for status, count in status_result.all()}
        
        # Priority breakdown
        priority_query = (
            select(CTA.priority, func.count(CTA.id))
            .where(CTA.project_id == project_id)
            .group_by(CTA.priority)
        )
        priority_result = await self.db.execute(priority_query)
        priority_breakdown = {priority: count for priority, count in priority_result.all()}
        
        # Business rules count
        business_rules_query = (
            select(func.count(CTA.id))
            .where(
                CTA.project_id == project_id,
                or_(
                    CTA.preconditions.isnot(None),
                    CTA.postconditions.isnot(None)
                )
            )
        )
        business_rules_result = await self.db.execute(business_rules_query)
        ctas_with_business_rules = business_rules_result.scalar() or 0
        
        # Story points stats
        story_points_query = (
            select(
                func.avg(CTA.story_points),
                func.sum(CTA.story_points)
            )
            .where(
                CTA.project_id == project_id,
                CTA.story_points.isnot(None)
            )
        )
        story_points_result = await self.db.execute(story_points_query)
        avg_story_points, total_story_points = story_points_result.first()
        
        # Unique roles and objects with CTAs
        roles_with_ctas_query = (
            select(func.count(func.distinct(CTA.role_id)))
            .where(CTA.project_id == project_id)
        )
        roles_with_ctas_result = await self.db.execute(roles_with_ctas_query)
        roles_with_ctas = roles_with_ctas_result.scalar() or 0
        
        objects_with_ctas_query = (
            select(func.count(func.distinct(CTA.object_id)))
            .where(CTA.project_id == project_id)
        )
        objects_with_ctas_result = await self.db.execute(objects_with_ctas_query)
        objects_with_ctas = objects_with_ctas_result.scalar() or 0
        
        return {
            'project_id': project_id,
            'total_ctas': total_ctas,
            'crud_breakdown': crud_breakdown,
            'status_breakdown': status_breakdown,
            'priority_breakdown': priority_breakdown,
            'roles_with_ctas': roles_with_ctas,
            'objects_with_ctas': objects_with_ctas,
            'ctas_with_business_rules': ctas_with_business_rules,
            'average_story_points': float(avg_story_points) if avg_story_points else None,
            'total_story_points': int(total_story_points) if total_story_points else None
        }
    
    # Private helper methods
    
    async def _validate_project_access(self, project_id: uuid.UUID, user_id: uuid.UUID):
        """Validate user has access to the project."""
        query = select(Project).where(Project.id == project_id)
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()
        
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
    
    async def _validate_cta_relationships(
        self, 
        project_id: uuid.UUID, 
        role_id: uuid.UUID, 
        object_id: uuid.UUID, 
        user_id: uuid.UUID
    ):
        """Validate that role and object belong to the project."""
        # Check role
        role_query = select(Role).where(
            Role.id == role_id, 
            Role.project_id == project_id
        )
        role_result = await self.db.execute(role_query)
        role = role_result.scalar_one_or_none()
        
        if not role:
            raise ValidationError(f"Role {role_id} not found in project {project_id}")
        
        # Check object
        object_query = select(Object).where(
            Object.id == object_id, 
            Object.project_id == project_id
        )
        object_result = await self.db.execute(object_query)
        obj = object_result.scalar_one_or_none()
        
        if not obj:
            raise ValidationError(f"Object {object_id} not found in project {project_id}")
    
    async def _validate_unique_cta(
        self, 
        project_id: uuid.UUID, 
        role_id: uuid.UUID, 
        object_id: uuid.UUID, 
        crud_type: CRUDType,
        exclude_id: Optional[uuid.UUID] = None
    ):
        """Validate CTA uniqueness within project."""
        query = (
            select(CTA)
            .where(
                CTA.project_id == project_id,
                CTA.role_id == role_id,
                CTA.object_id == object_id,
                CTA.crud_type == crud_type
            )
        )
        
        if exclude_id:
            query = query.where(CTA.id != exclude_id)
        
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValidationError(
                f"CTA already exists for role {role_id}, object {object_id}, "
                f"and CRUD type {crud_type}"
            )
    
    def _get_crud_action_text(self, crud_type: CRUDType) -> str:
        """Get human-readable action text for CRUD type."""
        return {
            CRUDType.CREATE: "create",
            CRUDType.READ: "view",
            CRUDType.UPDATE: "update", 
            CRUDType.DELETE: "delete"
        }.get(crud_type, "interact with")
