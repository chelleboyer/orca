"""
Test Epic 6.1 - Now/Next/Later Prioritization System
Tests the prioritization functionality for objects, CTAs, attributes, and relationships
"""

import pytest
import requests
import json
from typing import Dict, Any, List
from test_auth_service import get_test_user_token
from app.models.prioritization import PriorityPhase, ItemType


class TestEpic61Prioritization:
    """Test suite for Epic 6.1 prioritization features"""
    
    BASE_URL = "http://localhost:8000/api/v1"
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers for test requests"""
        token = get_test_user_token()
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def test_project_id(self, auth_headers):
        """Create a test project and return its ID"""
        # Create test project
        project_data = {
            "title": "Epic 6.1 Prioritization Test Project",
            "description": "Test project for prioritization features",
            "slug": "epic-61-prioritization-test"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/projects",
            json=project_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        return response.json()["id"]
    
    @pytest.fixture
    def test_objects(self, auth_headers, test_project_id):
        """Create test objects for prioritization"""
        objects = []
        
        for i in range(3):
            object_data = {
                "name": f"Test Object {i+1}",
                "definition": f"Definition for test object {i+1}",
                "complexity_level": "medium"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/projects/{test_project_id}/objects",
                json=object_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            objects.append(response.json())
        
        return objects
    
    @pytest.fixture
    def test_ctas(self, auth_headers, test_project_id, test_objects):
        """Create test CTAs for prioritization"""
        ctas = []
        
        for obj in test_objects[:2]:  # Create CTAs for first 2 objects
            cta_data = {
                "name": f"test_action",
                "object_name": obj["name"],
                "trigger": "User clicks button",
                "business_rules": "Must be authenticated",
                "functional_rules": "Validate input",
                "outputs": "Success message"
            }
            
            response = requests.post(
                f"{self.BASE_URL}/projects/{test_project_id}/objects/{obj['id']}/ctas",
                json=cta_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            ctas.append(response.json())
        
        return ctas
    
    def test_create_prioritization_object(self, auth_headers, test_project_id, test_objects):
        """Test creating prioritization for an object"""
        
        test_object = test_objects[0]
        prioritization_data = {
            "item_type": "object",
            "item_id": test_object["id"],
            "priority_phase": "now",
            "score": 8,
            "notes": "High priority object for first release"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
            json=prioritization_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        
        assert result["item_type"] == "object"
        assert result["item_id"] == test_object["id"]
        assert result["priority_phase"] == "now"
        assert result["score"] == 8
        assert result["notes"] == "High priority object for first release"
        assert result["project_id"] == test_project_id
        assert "id" in result
        assert "assigned_by" in result
        assert "assigned_at" in result
    
    def test_create_prioritization_cta(self, auth_headers, test_project_id, test_ctas):
        """Test creating prioritization for a CTA"""
        
        test_cta = test_ctas[0]
        prioritization_data = {
            "item_type": "cta",
            "item_id": test_cta["id"],
            "priority_phase": "next",
            "score": 6,
            "notes": "Important action for second phase"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
            json=prioritization_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        
        assert result["item_type"] == "cta"
        assert result["item_id"] == test_cta["id"]
        assert result["priority_phase"] == "next"
        assert result["score"] == 6
    
    def test_get_prioritizations_list(self, auth_headers, test_project_id, test_objects):
        """Test getting list of prioritizations with filtering"""
        
        # Create multiple prioritizations
        prioritizations = []
        for i, obj in enumerate(test_objects):
            phase = ["now", "next", "later"][i]
            prioritization_data = {
                "item_type": "object",
                "item_id": obj["id"],
                "priority_phase": phase,
                "score": (i + 1) * 3
            }
            
            response = requests.post(
                f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
                json=prioritization_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            prioritizations.append(response.json())
        
        # Test getting all prioritizations
        response = requests.get(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "items" in result
        assert "total" in result
        assert result["total"] == 3
        assert len(result["items"]) == 3
        
        # Test filtering by phase
        response = requests.get(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations?priority_phase=now",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["total"] == 1
        assert result["items"][0]["priority_phase"] == "now"
        
        # Test filtering by item type
        response = requests.get(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations?item_type=object",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["total"] == 3
        for item in result["items"]:
            assert item["item_type"] == "object"
    
    def test_get_prioritization_board(self, auth_headers, test_project_id, test_objects, test_ctas):
        """Test getting prioritization board organized by phases"""
        
        # Create prioritizations across different phases
        prioritizations_data = [
            {
                "item_type": "object",
                "item_id": test_objects[0]["id"],
                "priority_phase": "now",
                "score": 9
            },
            {
                "item_type": "object", 
                "item_id": test_objects[1]["id"],
                "priority_phase": "next",
                "score": 7
            },
            {
                "item_type": "cta",
                "item_id": test_ctas[0]["id"],
                "priority_phase": "later",
                "score": 5
            }
        ]
        
        for data in prioritizations_data:
            response = requests.post(
                f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
                json=data,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Get the prioritization board
        response = requests.get(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations/board",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        board = response.json()
        
        assert "now" in board
        assert "next" in board
        assert "later" in board
        assert "unassigned" in board
        
        assert len(board["now"]) == 1
        assert len(board["next"]) == 1
        assert len(board["later"]) == 1
        
        # Check that unassigned items include the unprioritized objects/CTAs
        assert len(board["unassigned"]) > 0
        
        # Verify items are in correct phases
        assert board["now"][0]["priority_phase"] == "now"
        assert board["next"][0]["priority_phase"] == "next"
        assert board["later"][0]["priority_phase"] == "later"
    
    def test_get_prioritization_stats(self, auth_headers, test_project_id, test_objects, test_ctas):
        """Test getting prioritization statistics"""
        
        # Create some prioritizations
        prioritizations_data = [
            {
                "item_type": "object",
                "item_id": test_objects[0]["id"],
                "priority_phase": "now",
                "score": 9
            },
            {
                "item_type": "object",
                "item_id": test_objects[1]["id"],
                "priority_phase": "now",
                "score": 8
            },
            {
                "item_type": "cta",
                "item_id": test_ctas[0]["id"],
                "priority_phase": "next",
                "score": 6
            }
        ]
        
        for data in prioritizations_data:
            response = requests.post(
                f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
                json=data,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Get prioritization statistics
        response = requests.get(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_items" in stats
        assert "prioritized_items" in stats
        assert "now_count" in stats
        assert "next_count" in stats
        assert "later_count" in stats
        assert "unassigned_count" in stats
        assert "by_item_type" in stats
        assert "average_score" in stats
        assert "scored_items" in stats
        
        assert stats["prioritized_items"] == 3
        assert stats["now_count"] == 2
        assert stats["next_count"] == 1
        assert stats["later_count"] == 0
        assert stats["scored_items"] == 3
        assert stats["average_score"] == pytest.approx(7.67, abs=0.1)  # (9+8+6)/3
        
        # Check by_item_type breakdown
        assert "object" in stats["by_item_type"]
        assert "cta" in stats["by_item_type"]
        assert stats["by_item_type"]["object"]["now"] == 2
        assert stats["by_item_type"]["cta"]["next"] == 1
    
    def test_update_prioritization(self, auth_headers, test_project_id, test_objects):
        """Test updating a prioritization"""
        
        # Create a prioritization
        test_object = test_objects[0]
        prioritization_data = {
            "item_type": "object",
            "item_id": test_object["id"],
            "priority_phase": "later",
            "score": 4
        }
        
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
            json=prioritization_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        prioritization = response.json()
        
        # Update the prioritization
        update_data = {
            "priority_phase": "now",
            "score": 9,
            "notes": "Moved to high priority"
        }
        
        response = requests.put(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations/{prioritization['id']}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        updated = response.json()
        
        assert updated["priority_phase"] == "now"
        assert updated["score"] == 9
        assert updated["notes"] == "Moved to high priority"
        assert updated["id"] == prioritization["id"]
    
    def test_bulk_update_prioritizations(self, auth_headers, test_project_id, test_objects):
        """Test bulk updating prioritizations (drag-and-drop simulation)"""
        
        # Create initial prioritizations
        prioritizations = []
        for i, obj in enumerate(test_objects):
            prioritization_data = {
                "item_type": "object",
                "item_id": obj["id"],
                "priority_phase": "unassigned",
                "score": 5
            }
            
            response = requests.post(
                f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
                json=prioritization_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            prioritizations.append(response.json())
        
        # Simulate drag-and-drop bulk update
        bulk_update_data = {
            "updates": [
                {
                    "item_id": test_objects[0]["id"],
                    "item_type": "object",
                    "priority_phase": "now",
                    "position": 1,
                    "score": 9
                },
                {
                    "item_id": test_objects[1]["id"],
                    "item_type": "object",
                    "priority_phase": "now",
                    "position": 2,
                    "score": 8
                },
                {
                    "item_id": test_objects[2]["id"],
                    "item_type": "object",
                    "priority_phase": "next",
                    "position": 1,
                    "score": 6
                }
            ]
        }
        
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations/bulk-update",
            json=bulk_update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        updated_prioritizations = response.json()
        
        assert len(updated_prioritizations) == 3
        
        # Verify updates were applied
        for updated in updated_prioritizations:
            if updated["item_id"] == test_objects[0]["id"]:
                assert updated["priority_phase"] == "now"
                assert updated["position"] == 1
                assert updated["score"] == 9
            elif updated["item_id"] == test_objects[1]["id"]:
                assert updated["priority_phase"] == "now"
                assert updated["position"] == 2
                assert updated["score"] == 8
            elif updated["item_id"] == test_objects[2]["id"]:
                assert updated["priority_phase"] == "next"
                assert updated["position"] == 1
                assert updated["score"] == 6
    
    def test_create_prioritization_snapshot(self, auth_headers, test_project_id, test_objects):
        """Test creating a prioritization snapshot"""
        
        # Create some prioritizations
        for i, obj in enumerate(test_objects):
            prioritization_data = {
                "item_type": "object",
                "item_id": obj["id"],
                "priority_phase": ["now", "next", "later"][i],
                "score": (i + 1) * 3
            }
            
            response = requests.post(
                f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
                json=prioritization_data,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Create a snapshot
        snapshot_data = {
            "snapshot_name": "Release 1 Planning",
            "description": "Initial prioritization for release 1"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations/snapshots",
            json=snapshot_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        snapshot = response.json()
        
        assert snapshot["snapshot_name"] == "Release 1 Planning"
        assert snapshot["description"] == "Initial prioritization for release 1"
        assert snapshot["project_id"] == test_project_id
        assert "id" in snapshot
        assert "created_by" in snapshot
        assert "created_at" in snapshot
        assert "snapshot_data" in snapshot
        
        # Verify snapshot data contains current prioritizations
        snapshot_data_parsed = json.loads(snapshot["snapshot_data"])
        assert len(snapshot_data_parsed) == 3
    
    def test_delete_prioritization(self, auth_headers, test_project_id, test_objects):
        """Test deleting a prioritization"""
        
        # Create a prioritization
        test_object = test_objects[0]
        prioritization_data = {
            "item_type": "object",
            "item_id": test_object["id"],
            "priority_phase": "now",
            "score": 8
        }
        
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
            json=prioritization_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        prioritization = response.json()
        
        # Delete the prioritization
        response = requests.delete(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations/{prioritization['id']}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify it's deleted
        response = requests.get(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations/{prioritization['id']}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_prioritization_validation(self, auth_headers, test_project_id, test_objects):
        """Test prioritization validation rules"""
        
        test_object = test_objects[0]
        
        # Test invalid score (too high)
        prioritization_data = {
            "item_type": "object",
            "item_id": test_object["id"],
            "priority_phase": "now",
            "score": 15  # Should be 1-10
        }
        
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
            json=prioritization_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        
        # Test invalid score (too low)
        prioritization_data["score"] = 0
        
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
            json=prioritization_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        
        # Test duplicate prioritization
        valid_data = {
            "item_type": "object",
            "item_id": test_object["id"],
            "priority_phase": "now",
            "score": 8
        }
        
        # First creation should succeed
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
            json=valid_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Second creation should fail (duplicate)
        response = requests.post(
            f"{self.BASE_URL}/projects/{test_project_id}/prioritizations",
            json=valid_data,
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_prioritization_permissions(self):
        """Test prioritization endpoints require authentication"""
        
        # Test without authentication
        response = requests.get(
            f"{self.BASE_URL}/projects/test-id/prioritizations"
        )
        
        assert response.status_code == 401


if __name__ == "__main__":
    # Quick validation test
    print("🧪 Epic 6.1 Prioritization Test Suite")
    print("=" * 50)
    
    # Test basic imports
    try:
        from app.models.prioritization import Prioritization, PrioritizationSnapshot, PriorityPhase, ItemType
        from app.services.prioritization_service import PrioritizationService
        from app.schemas.prioritization import PrioritizationResponse, PrioritizationCreate
        print("✅ All prioritization imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        exit(1)
    
    # Test enum values
    print("\n📋 Testing enum values:")
    print(f"Priority Phases: {[phase.value for phase in PriorityPhase]}")
    print(f"Item Types: {[item_type.value for item_type in ItemType]}")
    
    print("\n🚀 Epic 6.1 implementation ready for testing!")
    print("Run with: python -m pytest test_epic_6_1.py -v")
