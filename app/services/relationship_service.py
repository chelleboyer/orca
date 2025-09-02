"""
Service layer for relationship management operations.
Handles business logic for OOUX relationship mapping and NOM matrix.
"""
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid

from app.models.relationship import Relationship, RelationshipLock, UserPresence, CardinalityType
from app.models.object import Object
from app.schemas.relationship import (
    RelationshipCreate, RelationshipUpdate, RelationshipSearchRequest,
    MatrixCellData, MatrixObjectData, NOMMatrixResponse,
    RelationshipLockRequest, PresenceUpdateRequest
)
from app.core.exceptions import ValidationError, ConflictError


class RelationshipService:
    """Service for managing OOUX relationships and NOM matrix."""

    def __init__(self, db: Session):
        self.db = db

    def create_relationship(self, project_id: str, relationship_data: RelationshipCreate, user_id: str) -> Relationship:
        """
        Create a new relationship between objects.
        
        Args:
            project_id: UUID of the project
            relationship_data: Relationship creation data
            user_id: UUID of the creating user
            
        Returns:
            Created relationship instance
            
        Raises:
            ConflictError: If relationship already exists
            ValidationError: If data validation fails
        """
        # Check if relationship already exists
        existing = self.db.query(Relationship).filter(
            and_(
                Relationship.project_id == project_id,
                Relationship.source_object_id == relationship_data.source_object_id,
                Relationship.target_object_id == relationship_data.target_object_id
            )
        ).first()
        
        if existing:
            raise ConflictError("Relationship between these objects already exists")
        
        # Verify both objects exist and belong to the project
        source_obj = self.db.query(Object).filter(
            and_(Object.id == relationship_data.source_object_id, Object.project_id == project_id)
        ).first()
        
        target_obj = self.db.query(Object).filter(
            and_(Object.id == relationship_data.target_object_id, Object.project_id == project_id)
        ).first()
        
        if not source_obj or not target_obj:
            raise ValidationError("Source or target object not found in project")

        try:
            db_relationship = Relationship(
                project_id=project_id,
                source_object_id=relationship_data.source_object_id,
                target_object_id=relationship_data.target_object_id,
                cardinality=relationship_data.cardinality,
                forward_label=relationship_data.forward_label,
                reverse_label=relationship_data.reverse_label,
                is_bidirectional=relationship_data.is_bidirectional,
                description=relationship_data.description,
                strength=relationship_data.strength or "normal",
                created_by=user_id,
                updated_by=user_id
            )
            
            self.db.add(db_relationship)
            self.db.commit()
            self.db.refresh(db_relationship)
            
            return db_relationship
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create relationship: {str(e)}")

    def get_relationship(self, relationship_id: str, project_id: str) -> Optional[Relationship]:
        """
        Get a specific relationship by ID within a project.
        
        Args:
            relationship_id: UUID of the relationship
            project_id: UUID of the project
            
        Returns:
            Relationship instance or None if not found
        """
        return self.db.query(Relationship).filter(
            and_(
                Relationship.id == relationship_id,
                Relationship.project_id == project_id
            )
        ).first()

    def update_relationship(self, relationship_id: str, project_id: str, relationship_data: RelationshipUpdate, user_id: str) -> Optional[Relationship]:
        """
        Update an existing relationship.
        
        Args:
            relationship_id: UUID of the relationship
            project_id: UUID of the project
            relationship_data: Relationship update data
            user_id: UUID of the updating user
            
        Returns:
            Updated relationship instance or None if not found
        """
        db_relationship = self.get_relationship(relationship_id, project_id)
        if not db_relationship:
            return None

        try:
            # Update fields
            update_data = relationship_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_relationship, field, value)
            
            db_relationship.updated_by = user_id
            
            self.db.commit()
            self.db.refresh(db_relationship)
            
            return db_relationship
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update relationship: {str(e)}")

    def delete_relationship(self, relationship_id: str, project_id: str) -> bool:
        """
        Delete a relationship.
        
        Args:
            relationship_id: UUID of the relationship
            project_id: UUID of the project
            
        Returns:
            True if deleted, False if not found
        """
        db_relationship = self.get_relationship(relationship_id, project_id)
        if not db_relationship:
            return False

        try:
            self.db.delete(db_relationship)
            self.db.commit()
            return True
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Cannot delete relationship: {str(e)}")

    def get_nom_matrix(self, project_id: str) -> NOMMatrixResponse:
        """
        Get the complete NOM matrix for a project.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Complete matrix data with objects and relationships
        """
        # Get all objects in the project
        objects = self.db.query(Object).filter(
            Object.project_id == project_id
        ).order_by(Object.name).all()

        # Get all relationships in the project
        relationships = self.db.query(Relationship).filter(
            Relationship.project_id == project_id
        ).all()

        # Build matrix data structure
        matrix_objects = []
        for obj in objects:
            outgoing_count = len([r for r in relationships if str(r.source_object_id) == str(obj.id)])
            incoming_count = len([r for r in relationships if str(r.target_object_id) == str(obj.id)])
            
            matrix_objects.append(MatrixObjectData(
                id=obj.id,
                name=obj.name,
                definition=obj.definition,
                synonym_count=len(obj.synonyms) if obj.synonyms else 0,
                outgoing_relationship_count=outgoing_count,
                incoming_relationship_count=incoming_count
            ))

        # Build matrix cells
        matrix_data = []
        for i, source_obj in enumerate(objects):
            row = []
            for j, target_obj in enumerate(objects):
                # Find relationship between these objects
                relationship = None
                for rel in relationships:
                    if (str(rel.source_object_id) == str(source_obj.id) and 
                        str(rel.target_object_id) == str(target_obj.id)):
                        relationship = rel
                        break

                is_self_ref = str(source_obj.id) == str(target_obj.id)
                
                cell_data = MatrixCellData(
                    source_object_id=source_obj.id,
                    target_object_id=target_obj.id,
                    relationship=relationship,
                    is_self_reference=is_self_ref,
                    can_edit=not is_self_ref,
                    is_locked=False,  # TODO: Check for locks
                    locked_by=None
                )
                row.append(cell_data)
            matrix_data.append(row)

        # Calculate completion percentage
        total_possible = len(objects) * (len(objects) - 1)  # Exclude self-references
        actual_relationships = len(relationships)
        completion_percentage = (actual_relationships / total_possible * 100) if total_possible > 0 else 0

        return NOMMatrixResponse(
            project_id=uuid.UUID(project_id),
            objects=matrix_objects,
            matrix_data=matrix_data,
            total_objects=len(objects),
            total_relationships=len(relationships),
            matrix_completion_percentage=completion_percentage
        )

    def search_relationships(self, project_id: str, search_request: RelationshipSearchRequest) -> Tuple[List[Relationship], int]:
        """
        Search and filter relationships within a project.
        
        Args:
            project_id: UUID of the project
            search_request: Search parameters
            
        Returns:
            Tuple of (relationships list, total count)
        """
        query = self.db.query(Relationship).filter(Relationship.project_id == project_id)
        
        # Apply filters
        if search_request.source_object_id:
            query = query.filter(Relationship.source_object_id == search_request.source_object_id)
        
        if search_request.target_object_id:
            query = query.filter(Relationship.target_object_id == search_request.target_object_id)
        
        if search_request.cardinality:
            query = query.filter(Relationship.cardinality == search_request.cardinality)
        
        if search_request.strength:
            query = query.filter(Relationship.strength == search_request.strength)
        
        if search_request.is_bidirectional is not None:
            query = query.filter(Relationship.is_bidirectional == search_request.is_bidirectional)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(Relationship, search_request.sort_by)
        if search_request.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        relationships = query.offset(search_request.offset).limit(search_request.limit).all()
        
        return relationships, total

    def get_project_relationships(self, project_id: str) -> List[Relationship]:
        """
        Get all relationships for a project.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            List of all relationships in the project
        """
        return self.db.query(Relationship).filter(
            Relationship.project_id == project_id
        ).order_by(Relationship.created_at.desc()).all()

    # Lock management methods

    def acquire_lock(self, project_id: str, lock_request: RelationshipLockRequest, user_id: str) -> Optional[RelationshipLock]:
        """
        Acquire a lock on a relationship for editing.
        
        Args:
            project_id: UUID of the project
            lock_request: Lock request data
            user_id: UUID of the user requesting the lock
            
        Returns:
            Lock instance if successful, None if already locked
        """
        # Check for existing lock
        existing_lock = self.db.query(RelationshipLock).filter(
            and_(
                RelationshipLock.source_object_id == lock_request.source_object_id,
                RelationshipLock.target_object_id == lock_request.target_object_id,
                RelationshipLock.expires_at > datetime.utcnow()
            )
        ).first()
        
        if existing_lock:
            return None  # Already locked
        
        # Create new lock (5 minute expiry)
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        lock = RelationshipLock(
            source_object_id=lock_request.source_object_id,
            target_object_id=lock_request.target_object_id,
            locked_by=user_id,
            expires_at=expires_at,
            session_id=lock_request.session_id,
            lock_type=lock_request.lock_type
        )
        
        try:
            self.db.add(lock)
            self.db.commit()
            self.db.refresh(lock)
            return lock
        except IntegrityError:
            self.db.rollback()
            return None

    def release_lock(self, lock_id: str, user_id: str) -> bool:
        """
        Release a relationship lock.
        
        Args:
            lock_id: UUID of the lock
            user_id: UUID of the user releasing the lock
            
        Returns:
            True if released, False if not found or not owned by user
        """
        lock = self.db.query(RelationshipLock).filter(
            and_(
                RelationshipLock.id == lock_id,
                RelationshipLock.locked_by == user_id
            )
        ).first()
        
        if not lock:
            return False
        
        self.db.delete(lock)
        self.db.commit()
        return True

    def cleanup_expired_locks(self) -> int:
        """
        Clean up expired locks.
        
        Returns:
            Number of locks cleaned up
        """
        expired_locks = self.db.query(RelationshipLock).filter(
            RelationshipLock.expires_at <= datetime.utcnow()
        ).all()
        
        count = len(expired_locks)
        for lock in expired_locks:
            self.db.delete(lock)
        
        self.db.commit()
        return count

    # Presence management methods

    def update_presence(self, project_id: str, user_id: str, session_id: str, presence_data: PresenceUpdateRequest) -> UserPresence:
        """
        Update user presence in the project.
        
        Args:
            project_id: UUID of the project
            user_id: UUID of the user
            session_id: Session identifier
            presence_data: Presence update data
            
        Returns:
            Updated presence instance
        """
        # Find or create presence record
        presence = self.db.query(UserPresence).filter(
            and_(
                UserPresence.project_id == project_id,
                UserPresence.user_id == user_id
            )
        ).first()
        
        if not presence:
            presence = UserPresence(
                project_id=project_id,
                user_id=user_id,
                session_id=session_id
            )
            self.db.add(presence)
        
        # Update presence data
        presence.session_id = session_id
        presence.current_object_id = presence_data.current_object_id
        presence.current_activity = presence_data.current_activity
        presence.matrix_row = presence_data.matrix_row
        presence.matrix_col = presence_data.matrix_col
        presence.last_seen = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(presence)
        return presence

    def get_active_presence(self, project_id: str) -> List[UserPresence]:
        """
        Get all active user presence in the project.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            List of active presence records
        """
        threshold = datetime.utcnow() - timedelta(minutes=5)
        return self.db.query(UserPresence).filter(
            and_(
                UserPresence.project_id == project_id,
                UserPresence.last_seen > threshold
            )
        ).all()

    def cleanup_inactive_presence(self) -> int:
        """
        Clean up inactive presence records.
        
        Returns:
            Number of presence records cleaned up
        """
        threshold = datetime.utcnow() - timedelta(hours=1)
        inactive_presence = self.db.query(UserPresence).filter(
            UserPresence.last_seen <= threshold
        ).all()
        
        count = len(inactive_presence)
        for presence in inactive_presence:
            self.db.delete(presence)
        
        self.db.commit()
        return count
