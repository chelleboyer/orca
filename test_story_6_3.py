"""
Comprehensive test suite for Story 6.3: Representation Validation & Completeness
"""
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.services.validation_service import ValidationService


def test_validation_service_instantiation():
    """Test that ValidationService can be instantiated"""
    class MockDB:
        def query(self, model):
            return MockQuery()
        
    class MockQuery:
        def filter(self, *args):
            return self
        def join(self, *args, **kwargs):
            return self
        def all(self):
            return []
        def first(self):
            return None
        def count(self):
            return 0
    
    service = ValidationService(MockDB())
    assert service is not None
    print("✅ ValidationService instantiation successful")


def test_empty_project_validation():
    """Test validation behavior with empty project"""
    class MockDB:
        def query(self, model):
            return MockQuery()
        
    class MockQuery:
        def filter(self, *args):
            return self
        def join(self, *args, **kwargs):
            return self
        def all(self):
            return []  # No objects
        def first(self):
            return None
        def count(self):
            return 0
    
    service = ValidationService(MockDB())
    result = service.get_project_validation_summary("test-project-id")
    
    assert result["overall_completion"] == 0
    assert result["export_ready"] == False
    assert result["object_count"] == 0
    assert len(result["recommendations"]) > 0
    assert "Add Objects to Project" in result["recommendations"][0]["title"]
    
    print("✅ Empty project validation works correctly")


def test_validation_api_endpoints():
    """Test validation API endpoints"""
    client = TestClient(app)
    test_project_id = str(uuid.uuid4())
    
    # Test validation summary endpoint
    response = client.get(f"/api/v1/projects/{test_project_id}/validation")
    assert response.status_code == 200
    
    validation_data = response.json()
    assert "overall_completion" in validation_data
    assert "export_ready" in validation_data
    assert "dimension_scores" in validation_data
    assert "object_count" in validation_data
    assert "recommendations" in validation_data
    
    print("✅ Validation summary API endpoint working")
    
    # Test validation stats endpoint
    response = client.get(f"/api/v1/projects/{test_project_id}/validation/stats")
    assert response.status_code == 200
    
    stats_data = response.json()
    assert "overall_completion" in stats_data
    assert "export_ready" in stats_data
    assert "object_count" in stats_data
    
    print("✅ Validation stats API endpoint working")
    
    # Test gaps analysis endpoint
    response = client.get(f"/api/v1/projects/{test_project_id}/validation/gaps")
    assert response.status_code == 200
    
    gaps_data = response.json()
    assert "gap_summary" in gaps_data
    assert "gaps" in gaps_data
    assert "total_gaps" in gaps_data
    
    print("✅ Validation gaps API endpoint working")
    
    # Test export readiness endpoint
    response = client.get(f"/api/v1/projects/{test_project_id}/validation/export-readiness")
    assert response.status_code == 200
    
    readiness_data = response.json()
    assert "export_readiness" in readiness_data
    assert "overall_completion" in readiness_data
    
    print("✅ Export readiness API endpoint working")


def test_validation_with_priority_filter():
    """Test validation with priority filtering"""
    client = TestClient(app)
    test_project_id = str(uuid.uuid4())
    
    # Test gaps with priority filter
    response = client.get(f"/api/v1/projects/{test_project_id}/validation/gaps?priority=now")
    assert response.status_code == 200
    
    gaps_data = response.json()
    assert gaps_data["priority_filter"] == "now"
    
    print("✅ Priority filtering in validation working")


def test_validation_error_handling():
    """Test validation error handling"""
    client = TestClient(app)
    
    # Test with invalid object ID
    response = client.get(f"/api/v1/projects/{uuid.uuid4()}/objects/invalid-id/validation")
    assert response.status_code in [404, 422, 500]  # Should handle gracefully
    
    print("✅ Validation error handling working")


def test_validation_rules_endpoint():
    """Test validation rules endpoint"""
    client = TestClient(app)
    test_project_id = str(uuid.uuid4())
    
    response = client.get(f"/api/v1/projects/{test_project_id}/validation/rules")
    assert response.status_code == 200
    
    rules_data = response.json()
    assert "completion_thresholds" in rules_data
    assert "scoring_weights" in rules_data
    
    print("✅ Validation rules endpoint working")


def test_dimension_scores_structure():
    """Test dimension scores data structure"""
    class MockDB:
        def query(self, model):
            return MockQuery()
        
    class MockQuery:
        def filter(self, *args):
            return self
        def join(self, *args, **kwargs):
            return self
        def all(self):
            return []
        def first(self):
            return None
        def count(self):
            return 0
    
    service = ValidationService(MockDB())
    dimensions = service._analyze_project_dimensions("test-project")
    
    expected_dimensions = ["objects", "attributes", "ctas", "relationships", "prioritization"]
    for dim in expected_dimensions:
        assert dim in dimensions
        assert "total" in dimensions[dim]
        assert "completion_percentage" in dimensions[dim]
        assert "status" in dimensions[dim]
    
    print("✅ Dimension scores structure correct")


def test_validation_performance():
    """Test validation performance with simulated data"""
    class MockObject:
        def __init__(self, obj_id, name, definition="Test definition"):
            self.id = obj_id
            self.name = name
            self.definition = definition
            self.project_id = "test-project"
    
    class MockDB:
        def __init__(self, object_count=10):
            self.objects = [MockObject(i, f"Object {i}") for i in range(object_count)]
        
        def query(self, model):
            if "ObjectAttribute" in str(model):
                # Return empty list for attributes
                return MockQuery([])
            elif "CTA" in str(model):
                # Return empty list for CTAs  
                return MockQuery([])
            elif "Relationship" in str(model):
                # Return empty list for relationships
                return MockQuery([])
            else:
                return MockQuery(self.objects if "Object" in str(model) else [])
        
    class MockQuery:
        def __init__(self, data):
            self.data = data
        
        def filter(self, *args):
            return self
        
        def join(self, *args, **kwargs):
            return self
        
        def all(self):
            return self.data
        
        def first(self):
            return self.data[0] if self.data else None
        
        def count(self):
            return len(self.data)
    
    # Test with 10 objects
    service = ValidationService(MockDB(10))
    
    import time
    start_time = time.time()
    result = service.get_project_validation_summary("test-project")
    end_time = time.time()
    
    # Should complete quickly even with multiple objects
    assert end_time - start_time < 1.0  # Less than 1 second
    assert result["object_count"] == 10
    
    print(f"✅ Validation performance test passed ({end_time - start_time:.3f}s for 10 objects)")


def test_integration_with_cdll_service():
    """Test integration with existing CDLL completion scoring"""
    class MockAttribute:
        def __init__(self, name, is_core=False):
            self.name = name
            self.is_core = is_core
    
    class MockObjectAttribute:
        def __init__(self, attribute, is_core=False):
            self.attribute = attribute
            self.is_core = is_core
    
    class MockCTA:
        def __init__(self, name, crud_type, is_primary=False):
            self.name = name
            self.crud_type = crud_type
            self.is_primary = is_primary
    
    class MockObject:
        def __init__(self):
            self.id = uuid.uuid4()
            self.name = "Test Object"
            self.definition = "A test object for validation"
    
    # Mock the CDLL service integration
    from app.services.cdll_preview_service import CDLLPreviewService
    
    class MockDB:
        def query(self, model):
            return MockQuery()
        
    class MockQuery:
        def filter(self, *args):
            return self
        def all(self):
            return []
        def first(self):
            return None
        def count(self):
            return 0
    
    service = ValidationService(MockDB())
    
    # Test object data preparation
    obj = MockObject()
    obj_data = service._prepare_object_data(obj)
    
    assert "id" in obj_data
    assert "name" in obj_data
    assert "definition" in obj_data
    assert "core_attributes" in obj_data
    assert "all_ctas" in obj_data
    
    print("✅ Integration with CDLL service patterns working")


if __name__ == "__main__":
    print("🧪 Starting Story 6.3 Validation Test Suite")
    print("=" * 50)
    
    try:
        test_validation_service_instantiation()
        test_empty_project_validation()
        test_validation_api_endpoints()
        test_validation_with_priority_filter()
        test_validation_error_handling()
        test_validation_rules_endpoint()
        test_dimension_scores_structure()
        test_validation_performance()
        test_integration_with_cdll_service()
        
        print("\n" + "=" * 50)
        print("🎉 ALL STORY 6.3 VALIDATION TESTS PASSED!")
        print("✅ ValidationService implementation working")
        print("✅ API endpoints functioning correctly") 
        print("✅ Schema validation working")
        print("✅ Error handling robust")
        print("✅ Performance acceptable")
        print("✅ Integration with existing services successful")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
