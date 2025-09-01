"""
Service layer for object management operations.
Handles business logic for OOUX domain objects.
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.object import Object, ObjectSynonym, ObjectState
from app.schemas.object import (
    ObjectCreate, ObjectUpdate, ObjectSearchRequest,
    ObjectSynonymCreate, ObjectStateCreate
)
from app.core.exceptions import ValidationError, ConflictError


class ObjectService:
    """Service for managing OOUX domain objects."""

    def __init__(self, db: Session):
        self.db = db

    def create_object(self, project_id: str, object_data: ObjectCreate, user_id: str) -> Object:
        """
        Create a new object in the project.
        
        Args:
            project_id: UUID of the project
            object_data: Object creation data
            user_id: UUID of the creating user
            
        Returns:
            Created object instance
            
        Raises:
            ConflictError: If object name already exists in project
            ValidationError: If data validation fails
        """
        # Check if object name already exists in project
        existing = self.db.query(Object).filter(
            and_(
                Object.project_id == project_id,
                func.lower(Object.name) == func.lower(object_data.name.strip())
            )
        ).first()
        
        if existing:
            raise ConflictError(f"Object with name '{object_data.name}' already exists in this project")
        
        try:
            db_object = Object(
                project_id=project_id,
                name=object_data.name.strip(),
                definition=object_data.definition.strip() if object_data.definition else None,
                created_by=user_id,
                updated_by=user_id
            )
            
            self.db.add(db_object)
            self.db.commit()
            self.db.refresh(db_object)
            
            return db_object
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create object: {str(e)}")

    def get_object(self, object_id: str, project_id: str) -> Optional[Object]:
        """
        Get a specific object by ID within a project.
        
        Args:
            object_id: UUID of the object
            project_id: UUID of the project
            
        Returns:
            Object instance or None if not found
        """
        return self.db.query(Object).filter(
            and_(
                Object.id == object_id,
                Object.project_id == project_id
            )
        ).first()

    def update_object(self, object_id: str, project_id: str, object_data: ObjectUpdate, user_id: str) -> Optional[Object]:
        """
        Update an existing object.
        
        Args:
            object_id: UUID of the object
            project_id: UUID of the project
            object_data: Object update data
            user_id: UUID of the updating user
            
        Returns:
            Updated object instance or None if not found
            
        Raises:
            ConflictError: If updated name conflicts with existing object
            ValidationError: If data validation fails
        """
        db_object = self.get_object(object_id, project_id)
        if not db_object:
            return None

        # Check for name conflicts if name is being updated
        if object_data.name and object_data.name.strip() != db_object.name:
            existing = self.db.query(Object).filter(
                and_(
                    Object.project_id == project_id,
                    Object.id != object_id,
                    func.lower(Object.name) == func.lower(object_data.name.strip())
                )
            ).first()
            
            if existing:
                raise ConflictError(f"Object with name '{object_data.name}' already exists in this project")

        try:
            # Update fields
            if object_data.name is not None:
                db_object.name = object_data.name.strip()
            if object_data.definition is not None:
                db_object.definition = object_data.definition.strip() if object_data.definition else None
            
            db_object.updated_by = user_id
            
            self.db.commit()
            self.db.refresh(db_object)
            
            return db_object
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update object: {str(e)}")

    def delete_object(self, object_id: str, project_id: str) -> bool:
        """
        Delete an object and all its related data.
        
        Args:
            object_id: UUID of the object
            project_id: UUID of the project
            
        Returns:
            True if deleted, False if not found
            
        Note:
            This will cascade delete all synonyms and states.
            Future: Check for dependencies (relationships, attributes, etc.)
        """
        db_object = self.get_object(object_id, project_id)
        if not db_object:
            return False

        try:
            # Future: Add dependency checking here
            # - Check for relationships in NOM
            # - Check for CTAs in CTA Matrix
            # - Check for attributes
            
            self.db.delete(db_object)
            self.db.commit()
            
            return True
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Cannot delete object due to dependencies: {str(e)}")

    def search_objects(self, project_id: str, search_request: ObjectSearchRequest) -> Tuple[List[Object], int]:
        """
        Search and filter objects within a project.
        
        Args:
            project_id: UUID of the project
            search_request: Search parameters
            
        Returns:
            Tuple of (objects list, total count)
        """
        query = self.db.query(Object).filter(Object.project_id == project_id)
        
        # Apply search filter
        if search_request.query:
            search_term = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    Object.name.ilike(search_term),
                    Object.definition.ilike(search_term),
                    Object.synonyms.any(ObjectSynonym.synonym.ilike(search_term))
                )
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(Object, search_request.sort_by)
        if search_request.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        objects = query.offset(search_request.offset).limit(search_request.limit).all()
        
        return objects, total

    def get_project_objects(self, project_id: str) -> List[Object]:
        """
        Get all objects for a project.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            List of all objects in the project
        """
        return self.db.query(Object).filter(
            Object.project_id == project_id
        ).order_by(Object.name).all()

    # Synonym management methods

    def add_synonym(self, object_id: str, project_id: str, synonym_data: ObjectSynonymCreate, user_id: str) -> ObjectSynonym:
        """
        Add a synonym to an object.
        
        Args:
            object_id: UUID of the object
            project_id: UUID of the project
            synonym_data: Synonym creation data
            user_id: UUID of the creating user
            
        Returns:
            Created synonym instance
            
        Raises:
            ValidationError: If object not found or synonym already exists
        """
        # Verify object exists
        db_object = self.get_object(object_id, project_id)
        if not db_object:
            raise ValidationError("Object not found")

        # Check if synonym already exists for this object
        existing = self.db.query(ObjectSynonym).filter(
            and_(
                ObjectSynonym.object_id == object_id,
                func.lower(ObjectSynonym.synonym) == func.lower(synonym_data.synonym.strip())
            )
        ).first()
        
        if existing:
            raise ConflictError(f"Synonym '{synonym_data.synonym}' already exists for this object")

        try:
            db_synonym = ObjectSynonym(
                object_id=object_id,
                synonym=synonym_data.synonym.strip(),
                created_by=user_id
            )
            
            self.db.add(db_synonym)
            self.db.commit()
            self.db.refresh(db_synonym)
            
            return db_synonym
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create synonym: {str(e)}")

    def remove_synonym(self, synonym_id: str, object_id: str, project_id: str) -> bool:
        """
        Remove a synonym from an object.
        
        Args:
            synonym_id: UUID of the synonym
            object_id: UUID of the object
            project_id: UUID of the project
            
        Returns:
            True if removed, False if not found
        """
        synonym = self.db.query(ObjectSynonym).join(Object).filter(
            and_(
                ObjectSynonym.id == synonym_id,
                ObjectSynonym.object_id == object_id,
                Object.project_id == project_id
            )
        ).first()
        
        if not synonym:
            return False

        self.db.delete(synonym)
        self.db.commit()
        
        return True

    # State management methods

    def add_state(self, object_id: str, project_id: str, state_data: ObjectStateCreate, user_id: str) -> ObjectState:
        """
        Add a state to an object.
        
        Args:
            object_id: UUID of the object
            project_id: UUID of the project
            state_data: State creation data
            user_id: UUID of the creating user
            
        Returns:
            Created state instance
            
        Raises:
            ValidationError: If object not found or state name already exists
        """
        # Verify object exists
        db_object = self.get_object(object_id, project_id)
        if not db_object:
            raise ValidationError("Object not found")

        # Check if state name already exists for this object
        existing = self.db.query(ObjectState).filter(
            and_(
                ObjectState.object_id == object_id,
                func.lower(ObjectState.state_name) == func.lower(state_data.state_name.strip())
            )
        ).first()
        
        if existing:
            raise ConflictError(f"State '{state_data.state_name}' already exists for this object")

        try:
            db_state = ObjectState(
                object_id=object_id,
                state_name=state_data.state_name.strip(),
                description=state_data.description.strip() if state_data.description else None,
                order_index=state_data.order_index,
                created_by=user_id
            )
            
            self.db.add(db_state)
            self.db.commit()
            self.db.refresh(db_state)
            
            return db_state
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create state: {str(e)}")

    def remove_state(self, state_id: str, object_id: str, project_id: str) -> bool:
        """
        Remove a state from an object.
        
        Args:
            state_id: UUID of the state
            object_id: UUID of the object
            project_id: UUID of the project
            
        Returns:
            True if removed, False if not found
        """
        state = self.db.query(ObjectState).join(Object).filter(
            and_(
                ObjectState.id == state_id,
                ObjectState.object_id == object_id,
                Object.project_id == project_id
            )
        ).first()
        
        if not state:
            return False

        self.db.delete(state)
        self.db.commit()
        
        return True
