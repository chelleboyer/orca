"""
Attribute service for managing project attributes and object attribute values
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, asc
from fastapi import HTTPException, status
import uuid
import json

from app.models.attribute import Attribute, AttributeType, ObjectAttribute
from app.models.object import Object
from app.models.project import Project
from app.schemas.attribute import (
    AttributeCreate, AttributeUpdate, AttributeFilterParams,
    ObjectAttributeCreate
)


class AttributeService:
    """Service for managing attributes and object attribute values"""

    def __init__(self, db: Session):
        self.db = db

    # Attribute CRUD operations
    def create_attribute(self, attribute_data: AttributeCreate) -> Attribute:
        """Create a new attribute"""
        # Verify project exists
        project = self.db.query(Project).filter(Project.id == attribute_data.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check for duplicate attribute names within project
        existing = self.db.query(Attribute).filter(
            and_(
                Attribute.project_id == attribute_data.project_id,
                Attribute.name == attribute_data.name,
                Attribute.is_active.is_(True)
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attribute '{attribute_data.name}' already exists in this project"
            )

        # Validate reference object if specified
        if attribute_data.reference_object_id:
            if attribute_data.data_type != AttributeType.REFERENCE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="reference_object_id can only be set for REFERENCE type attributes"
                )

            ref_object = self.db.query(Object).filter(
                and_(
                    Object.id == attribute_data.reference_object_id,
                    Object.project_id == attribute_data.project_id
                )
            ).first()

            if not ref_object:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Referenced object not found in this project"
                )

        # Validate list options for LIST type
        if attribute_data.data_type == AttributeType.LIST and attribute_data.list_options:
            try:
                options = json.loads(attribute_data.list_options)
                if not isinstance(options, list) or not all(isinstance(opt, str) for opt in options):
                    raise ValueError("List options must be a JSON array of strings")
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid list_options format: {str(e)}"
                )

        # Create the attribute
        db_attribute = Attribute(
            name=attribute_data.name,
            description=attribute_data.description,
            data_type=attribute_data.data_type,
            is_core=attribute_data.is_core,
            reference_object_id=attribute_data.reference_object_id,
            list_options=attribute_data.list_options,
            is_active=attribute_data.is_active,
            project_id=attribute_data.project_id
        )

        self.db.add(db_attribute)
        self.db.commit()
        self.db.refresh(db_attribute)

        return db_attribute

    def get_attribute(self, attribute_id: uuid.UUID, project_id: uuid.UUID) -> Optional[Attribute]:
        """Get an attribute by ID within a project"""
        return self.db.query(Attribute).filter(
            and_(
                Attribute.id == attribute_id,
                Attribute.project_id == project_id
            )
        ).first()

    def get_project_attributes(
        self,
        project_id: uuid.UUID,
        filters: Optional[AttributeFilterParams] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Attribute], int]:
        """Get attributes for a project with filtering and pagination"""
        query = self.db.query(Attribute).filter(
            Attribute.project_id == project_id,
            Attribute.is_active.is_(True)
        )

        # Apply filters if provided
        if filters:
            if filters.name:
                query = query.filter(Attribute.name.ilike(f"%{filters.name}%"))

            if filters.data_type:
                query = query.filter(Attribute.data_type == filters.data_type)

            if filters.is_core is not None:
                query = query.filter(Attribute.is_core == filters.is_core)

        # Get total count for pagination
        total = query.count()

        # Apply ordering
        if filters and filters.sort_by:
            if filters.sort_order == 'desc':
                query = query.order_by(desc(getattr(Attribute, filters.sort_by)))
            else:
                query = query.order_by(asc(getattr(Attribute, filters.sort_by)))
        else:
            query = query.order_by(Attribute.name)

        # Apply pagination
        attributes = query.offset(skip).limit(limit).all()

        return attributes, total

    def update_attribute(self, attribute_id: uuid.UUID, project_id: uuid.UUID, update_data: AttributeUpdate) -> Optional[Attribute]:
        """Update an existing attribute"""
        attribute = self.get_attribute(attribute_id, project_id)
        if not attribute:
            return None

        # Check for name conflicts if name is being updated
        if update_data.name and update_data.name != attribute.name:
            existing = self.db.query(Attribute).filter(
                and_(
                    Attribute.project_id == project_id,
                    Attribute.name == update_data.name,
                    Attribute.id != attribute_id,
                    Attribute.is_active .is_(True)
                )
            ).first()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Attribute '{update_data.name}' already exists in this project"
                )

        # Validate reference object if being updated
        if update_data.reference_object_id is not None:
            new_data_type = update_data.data_type if update_data.data_type else attribute.data_type
            if new_data_type != AttributeType.REFERENCE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="reference_object_id can only be set for REFERENCE type attributes"
                )

            if update_data.reference_object_id:  # Not None and not empty
                ref_object = self.db.query(Object).filter(
                    and_(
                        Object.id == update_data.reference_object_id,
                        Object.project_id == project_id
                    )
                ).first()

                if not ref_object:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Referenced object not found in this project"
                    )

        # Update fields
        update_fields = update_data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(attribute, field, value)

        self.db.commit()
        self.db.refresh(attribute)

        return attribute

    def delete_attribute(self, attribute_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Soft delete an attribute (set is_active=False)"""
        attribute = self.get_attribute(attribute_id, project_id)
        if not attribute:
            return False

        attribute.is_active = False
        self.db.commit()

        return True

    def bulk_create_attributes(self, attributes_data: List[AttributeCreate]) -> List[Attribute]:
        """Create multiple attributes in bulk"""
        created_attributes = []

        for attr_data in attributes_data:
            try:
                attribute = self.create_attribute(attr_data)
                created_attributes.append(attribute)
            except HTTPException:
                # Rollback and re-raise on any validation error
                self.db.rollback()
                raise

        return created_attributes

    # Object Attribute operations
    def set_object_attribute_value(self, obj_attr_data: ObjectAttributeCreate) -> ObjectAttribute:
        """Set or update an object's attribute value"""
        # Verify object and attribute exist and belong to same project
        obj = self.db.query(Object).filter(Object.id == obj_attr_data.object_id).first()
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Object not found"
            )

        attribute = self.db.query(Attribute).filter(
            and_(
                Attribute.id == obj_attr_data.attribute_id,
                Attribute.project_id == obj.project_id,
                Attribute.is_active .is_(True)
            )
        ).first()

        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute not found or not active"
            )

        # Check if object attribute already exists
        existing = self.db.query(ObjectAttribute).filter(
            and_(
                ObjectAttribute.object_id == obj_attr_data.object_id,
                ObjectAttribute.attribute_id == obj_attr_data.attribute_id
            )
        ).first()

        if existing:
            # Update existing value
            existing.value = obj_attr_data.value
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new object attribute
            obj_attribute = ObjectAttribute(
                object_id=obj_attr_data.object_id,
                attribute_id=obj_attr_data.attribute_id,
                value=obj_attr_data.value
            )

            self.db.add(obj_attribute)
            self.db.commit()
            self.db.refresh(obj_attribute)

            return obj_attribute

    def get_object_attributes(self, object_id: uuid.UUID) -> List[ObjectAttribute]:
        """Get all attribute values for an object"""
        return self.db.query(ObjectAttribute).options(
            joinedload(ObjectAttribute.attribute)
        ).filter(
            ObjectAttribute.object_id == object_id
        ).all()

    def remove_object_attribute(self, object_id: uuid.UUID, attribute_id: uuid.UUID) -> bool:
        """Remove an object's attribute value"""
        obj_attr = self.db.query(ObjectAttribute).filter(
            and_(
                ObjectAttribute.object_id == object_id,
                ObjectAttribute.attribute_id == attribute_id
            )
        ).first()

        if obj_attr:
            self.db.delete(obj_attr)
            self.db.commit()
            return True

        return False

    def bulk_update_object_attributes(self, updates: List[Dict[str, Any]]) -> List[ObjectAttribute]:
        """Bulk update object attribute values"""
        updated_attributes = []

        for update in updates:
            obj_attr_data = ObjectAttributeCreate(
                object_id=update["object_id"],
                attribute_id=update["attribute_id"],
                value=update.get("value")
            )

            obj_attr = self.set_object_attribute_value(obj_attr_data)
            updated_attributes.append(obj_attr)

        return updated_attributes

    # Statistics and reporting
    def get_attribute_stats(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """Get statistics about attributes in a project"""
        # Basic counts
        total_query = self.db.query(Attribute).filter(Attribute.project_id == project_id)
        total_attributes = total_query.count()
        core_attributes = total_query.filter(Attribute.is_core .is_(True)).count()
        active_attributes = total_query.filter(Attribute.is_active .is_(True)).count()

        # Count by type
        type_counts = {}
        for attr_type in AttributeType:
            count = total_query.filter(Attribute.data_type == attr_type).count()
            type_counts[attr_type.value] = count

        # Usage statistics - how many objects use each attribute
        usage_stats = {}
        attributes = total_query.filter(Attribute.is_active .is_(True)).all()

        for attribute in attributes:
            usage_count = self.db.query(ObjectAttribute).filter(
                ObjectAttribute.attribute_id == attribute.id
            ).count()
            usage_stats[attribute.name] = usage_count

        return {
            "total_attributes": total_attributes,
            "core_attributes": core_attributes,
            "active_attributes": active_attributes,
            "by_type": type_counts,
            "usage_stats": usage_stats
        }
