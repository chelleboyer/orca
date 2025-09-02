"""
Tests for relationship management functionality.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.relationship import Relationship, RelationshipLock, UserPresence, CardinalityType
from app.models.object import Object
from app.models.project import Project
from app.models.user import User
from app.services.relationship_service import RelationshipService
from app.schemas.relationship import RelationshipCreate, RelationshipUpdate


class TestRelationshipService:
    """Test relationship service functionality."""

    def test_create_relationship(self, db_session: Session, sample_user: User, sample_project: Project):
        """Test creating a new relationship between objects."""
        # Create test objects
        obj1 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="User",
            definition="A person who uses the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        obj2 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="Account",
            definition="A user account in the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        db_session.add_all([obj1, obj2])
        db_session.commit()

        # Create relationship
        service = RelationshipService(db_session)
        relationship_data = RelationshipCreate(
            source_object_id=obj1.id,
            target_object_id=obj2.id,
            cardinality=CardinalityType.ONE_TO_ONE,
            forward_label="owns",
            reverse_label="owned by",
            is_bidirectional=True
        )
        
        relationship = service.create_relationship(
            str(sample_project.id), 
            relationship_data, 
            str(sample_user.id)
        )
        
        assert relationship is not None
        assert relationship.source_object_id == obj1.id
        assert relationship.target_object_id == obj2.id
        assert relationship.cardinality == CardinalityType.ONE_TO_ONE
        assert relationship.forward_label == "owns"
        assert relationship.reverse_label == "owned by"
        assert relationship.is_bidirectional is True

    def test_duplicate_relationship_error(self, db_session: Session, sample_user: User, sample_project: Project):
        """Test that creating duplicate relationships raises ConflictError."""
        # Create test objects
        obj1 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="User",
            definition="A person who uses the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        obj2 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="Account",
            definition="A user account in the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        db_session.add_all([obj1, obj2])
        db_session.commit()

        service = RelationshipService(db_session)
        relationship_data = RelationshipCreate(
            source_object_id=obj1.id,
            target_object_id=obj2.id,
            cardinality=CardinalityType.ONE_TO_ONE,
            forward_label="owns",
            reverse_label="owned by",
            is_bidirectional=True
        )
        
        # First creation should succeed
        service.create_relationship(
            str(sample_project.id), 
            relationship_data, 
            str(sample_user.id)
        )
        
        # Second creation should fail
        from app.core.exceptions import ConflictError
        with pytest.raises(ConflictError):
            service.create_relationship(
                str(sample_project.id), 
                relationship_data, 
                str(sample_user.id)
            )

    def test_get_nom_matrix(self, db_session: Session, sample_user: User, sample_project: Project):
        """Test retrieving the NOM matrix for a project."""
        # Create test objects
        objects = []
        for i in range(3):
            obj = Object(
                id=uuid.uuid4(),
                project_id=sample_project.id,
                name=f"Object{i+1}",
                definition=f"Test object {i+1}",
                created_by=sample_user.id,
                updated_by=sample_user.id
            )
            objects.append(obj)
        db_session.add_all(objects)
        db_session.commit()

        # Create relationships
        service = RelationshipService(db_session)
        relationship_data = RelationshipCreate(
            source_object_id=objects[0].id,
            target_object_id=objects[1].id,
            cardinality=CardinalityType.ONE_TO_MANY,
            forward_label="has",
            reverse_label="belongs to",
            is_bidirectional=False
        )
        
        service.create_relationship(
            str(sample_project.id), 
            relationship_data, 
            str(sample_user.id)
        )
        
        # Get matrix
        matrix = service.get_nom_matrix(str(sample_project.id))
        
        assert matrix.total_objects == 3
        assert matrix.total_relationships == 1
        assert len(matrix.objects) == 3
        assert len(matrix.matrix_data) == 3
        assert len(matrix.matrix_data[0]) == 3
        assert matrix.matrix_completion_percentage > 0

    def test_update_relationship(self, db_session: Session, sample_user: User, sample_project: Project):
        """Test updating an existing relationship."""
        # Create test objects
        obj1 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="User",
            definition="A person who uses the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        obj2 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="Account",
            definition="A user account in the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        db_session.add_all([obj1, obj2])
        db_session.commit()

        service = RelationshipService(db_session)
        
        # Create relationship
        relationship_data = RelationshipCreate(
            source_object_id=obj1.id,
            target_object_id=obj2.id,
            cardinality=CardinalityType.ONE_TO_ONE,
            forward_label="owns",
            reverse_label="owned by",
            is_bidirectional=True
        )
        
        relationship = service.create_relationship(
            str(sample_project.id), 
            relationship_data, 
            str(sample_user.id)
        )
        
        # Update relationship
        update_data = RelationshipUpdate(
            cardinality=CardinalityType.ONE_TO_MANY,
            forward_label="manages",
            description="Management relationship"
        )
        
        updated_relationship = service.update_relationship(
            str(relationship.id),
            str(sample_project.id),
            update_data,
            str(sample_user.id)
        )
        
        assert updated_relationship is not None
        assert updated_relationship.cardinality == CardinalityType.ONE_TO_MANY
        assert updated_relationship.forward_label == "manages"
        assert updated_relationship.description == "Management relationship"
        assert updated_relationship.reverse_label == "owned by"  # Should remain unchanged

    def test_delete_relationship(self, db_session: Session, sample_user: User, sample_project: Project):
        """Test deleting a relationship."""
        # Create test objects
        obj1 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="User",
            definition="A person who uses the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        obj2 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="Account",
            definition="A user account in the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        db_session.add_all([obj1, obj2])
        db_session.commit()

        service = RelationshipService(db_session)
        
        # Create relationship
        relationship_data = RelationshipCreate(
            source_object_id=obj1.id,
            target_object_id=obj2.id,
            cardinality=CardinalityType.ONE_TO_ONE,
            forward_label="owns",
            reverse_label="owned by",
            is_bidirectional=True
        )
        
        relationship = service.create_relationship(
            str(sample_project.id), 
            relationship_data, 
            str(sample_user.id)
        )
        
        # Delete relationship
        deleted = service.delete_relationship(
            str(relationship.id),
            str(sample_project.id)
        )
        
        assert deleted is True
        
        # Verify it's gone
        found = service.get_relationship(str(relationship.id), str(sample_project.id))
        assert found is None

    def test_acquire_and_release_lock(self, db_session: Session, sample_user: User, sample_project: Project):
        """Test acquiring and releasing relationship locks."""
        # Create test objects
        obj1 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="User",
            definition="A person who uses the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        obj2 = Object(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            name="Account",
            definition="A user account in the system",
            created_by=sample_user.id,
            updated_by=sample_user.id
        )
        db_session.add_all([obj1, obj2])
        db_session.commit()

        service = RelationshipService(db_session)
        
        from app.schemas.relationship import RelationshipLockRequest
        lock_request = RelationshipLockRequest(
            source_object_id=obj1.id,
            target_object_id=obj2.id,
            session_id="test-session-123",
            lock_type="edit"
        )
        
        # Acquire lock
        lock = service.acquire_lock(
            str(sample_project.id),
            lock_request,
            str(sample_user.id)
        )
        
        assert lock is not None
        assert lock.source_object_id == obj1.id
        assert lock.target_object_id == obj2.id
        assert lock.locked_by == sample_user.id
        assert lock.session_id == "test-session-123"
        
        # Try to acquire again (should fail)
        duplicate_lock = service.acquire_lock(
            str(sample_project.id),
            lock_request,
            str(sample_user.id)
        )
        
        assert duplicate_lock is None
        
        # Release lock
        released = service.release_lock(str(lock.id), str(sample_user.id))
        assert released is True

    def test_presence_management(self, db_session: Session, sample_user: User, sample_project: Project):
        """Test user presence tracking."""
        service = RelationshipService(db_session)
        
        from app.schemas.relationship import PresenceUpdateRequest
        presence_data = PresenceUpdateRequest(
            current_activity="editing",
            matrix_row=2,
            matrix_col=3
        )
        
        # Update presence
        presence = service.update_presence(
            str(sample_project.id),
            str(sample_user.id),
            "test-session-456",
            presence_data
        )
        
        assert presence is not None
        assert presence.project_id == sample_project.id
        assert presence.user_id == sample_user.id
        assert presence.current_activity == "editing"
        assert presence.matrix_row == 2
        assert presence.matrix_col == 3
        
        # Get active presence
        active_presence = service.get_active_presence(str(sample_project.id))
        assert len(active_presence) == 1
        assert active_presence[0].user_id == sample_user.id


class TestRelationshipAPI:
    """Test relationship API endpoints."""

    def test_create_relationship_endpoint(self, client: TestClient, auth_headers: dict, sample_project: Project):
        """Test creating a relationship via API."""
        # First create some objects
        obj1_data = {
            "name": "User",
            "definition": "A person who uses the system"
        }
        obj2_data = {
            "name": "Account", 
            "definition": "A user account in the system"
        }
        
        obj1_response = client.post(
            f"/api/v1/projects/{sample_project.id}/objects/",
            json=obj1_data,
            headers=auth_headers
        )
        obj2_response = client.post(
            f"/api/v1/projects/{sample_project.id}/objects/",
            json=obj2_data,
            headers=auth_headers
        )
        
        assert obj1_response.status_code == 201
        assert obj2_response.status_code == 201
        
        obj1_id = obj1_response.json()["id"]
        obj2_id = obj2_response.json()["id"]
        
        # Create relationship
        relationship_data = {
            "source_object_id": obj1_id,
            "target_object_id": obj2_id,
            "cardinality": "1:1",
            "forward_label": "owns",
            "reverse_label": "owned by",
            "is_bidirectional": True
        }
        
        response = client.post(
            f"/api/v1/projects/{sample_project.id}/relationships/",
            json=relationship_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["source_object_id"] == obj1_id
        assert data["target_object_id"] == obj2_id
        assert data["cardinality"] == "1:1"
        assert data["forward_label"] == "owns"

    def test_get_nom_matrix_endpoint(self, client: TestClient, auth_headers: dict, sample_project: Project):
        """Test getting the NOM matrix via API."""
        response = client.get(
            f"/api/v1/projects/{sample_project.id}/relationships/matrix/nom",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert "objects" in data
        assert "matrix_data" in data
        assert "total_objects" in data
        assert "total_relationships" in data
        assert "matrix_completion_percentage" in data
        
        assert data["project_id"] == str(sample_project.id)
        assert isinstance(data["objects"], list)
        assert isinstance(data["matrix_data"], list)

    def test_relationship_not_found(self, client: TestClient, auth_headers: dict, sample_project: Project):
        """Test accessing non-existent relationship."""
        fake_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/projects/{sample_project.id}/relationships/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
