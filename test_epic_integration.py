"""
Quick test to verify Epic 1, 2, and 3 integration.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test that the application is running."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_api_docs():
    """Test that API documentation is accessible."""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"✅ API docs accessible: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API docs failed: {e}")
        return False

def test_user_registration():
    """Test Epic 1: User registration functionality."""
    try:
        user_data = {
            "email": f"test-epic3-{hash('test')}@example.com",
            "password": "TestPassword123!",
            "display_name": "Epic 3 Test User"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
        print(f"✅ User registration: {response.status_code}")
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ User registration failed: {e}")
        return None

def test_user_login(user_data):
    """Test Epic 1: User login functionality."""
    try:
        login_data = {
            "email": user_data["email"],
            "password": "TestPassword123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"✅ User login: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ User login failed: {e}")
        return None

def test_project_creation(auth_token):
    """Test Epic 2: Project creation functionality."""
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        project_data = {
            "name": "Epic 3 Test Project",
            "description": "Testing relationship mapping functionality"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/projects/", json=project_data, headers=headers)
        print(f"✅ Project creation: {response.status_code}")
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Project creation failed: {e}")
        return None

def test_object_creation(auth_token, project_id):
    """Test Epic 2: Object creation functionality."""
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create first object
        obj1_data = {
            "name": "User",
            "definition": "A person who uses the system"
        }
        
        response1 = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/objects/", json=obj1_data, headers=headers)
        print(f"✅ Object 1 creation: {response1.status_code}")
        
        # Create second object
        obj2_data = {
            "name": "Account",
            "definition": "A user account in the system"
        }
        
        response2 = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/objects/", json=obj2_data, headers=headers)
        print(f"✅ Object 2 creation: {response2.status_code}")
        
        if response1.status_code == 201 and response2.status_code == 201:
            return response1.json(), response2.json()
        else:
            print(f"   Response 1: {response1.text}")
            print(f"   Response 2: {response2.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Object creation failed: {e}")
        return None, None

def test_relationship_creation(auth_token, project_id, obj1_id, obj2_id):
    """Test Epic 3: Relationship creation functionality."""
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        relationship_data = {
            "source_object_id": obj1_id,
            "target_object_id": obj2_id,
            "cardinality": "1:1",
            "forward_label": "owns",
            "reverse_label": "owned by",
            "is_bidirectional": True
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/relationships/", json=relationship_data, headers=headers)
        print(f"✅ Relationship creation: {response.status_code}")
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Relationship creation failed: {e}")
        return None

def test_nom_matrix(auth_token, project_id):
    """Test Epic 3: NOM matrix functionality."""
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/v1/projects/{project_id}/relationships/matrix/nom", headers=headers)
        print(f"✅ NOM matrix retrieval: {response.status_code}")
        
        if response.status_code == 200:
            matrix_data = response.json()
            print(f"   Objects: {matrix_data.get('total_objects', 0)}")
            print(f"   Relationships: {matrix_data.get('total_relationships', 0)}")
            print(f"   Completion: {matrix_data.get('matrix_completion_percentage', 0):.1f}%")
            return matrix_data
        else:
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ NOM matrix failed: {e}")
        return None

def main():
    """Run all integration tests."""
    print("🧪 Running Epic 1, 2, and 3 Integration Tests")
    print("=" * 50)
    
    # Test basic connectivity
    if not test_health():
        print("❌ Application not running!")
        return
    
    if not test_api_docs():
        print("❌ API documentation not accessible!")
        return
    
    # Test Epic 1: Authentication
    print("\n🔐 Testing Epic 1: Authentication")
    user_data = test_user_registration()
    if not user_data:
        print("❌ Epic 1 failed: Could not register user")
        return
    
    login_data = test_user_login(user_data)
    if not login_data:
        print("❌ Epic 1 failed: Could not login user")
        return
    
    auth_token = login_data.get("access_token")
    if not auth_token:
        print("❌ Epic 1 failed: No access token received")
        return
    
    print("✅ Epic 1: Authentication PASSED")
    
    # Test Epic 2: Object Management
    print("\n📦 Testing Epic 2: Object Management")
    project_data = test_project_creation(auth_token)
    if not project_data:
        print("❌ Epic 2 failed: Could not create project")
        return
    
    project_id = project_data.get("id")
    obj1_data, obj2_data = test_object_creation(auth_token, project_id)
    if not obj1_data or not obj2_data:
        print("❌ Epic 2 failed: Could not create objects")
        return
    
    print("✅ Epic 2: Object Management PASSED")
    
    # Test Epic 3: Relationship Mapping
    print("\n🔗 Testing Epic 3: Relationship Mapping")
    obj1_id = obj1_data.get("id")
    obj2_id = obj2_data.get("id")
    
    relationship_data = test_relationship_creation(auth_token, project_id, obj1_id, obj2_id)
    if not relationship_data:
        print("❌ Epic 3 failed: Could not create relationship")
        return
    
    matrix_data = test_nom_matrix(auth_token, project_id)
    if not matrix_data:
        print("❌ Epic 3 failed: Could not retrieve NOM matrix")
        return
    
    print("✅ Epic 3: Relationship Mapping PASSED")
    
    print("\n🎉 ALL EPICS INTEGRATION TEST PASSED!")
    print("✅ Epic 1: Foundation & Authentication - FUNCTIONAL")
    print("✅ Epic 2: Core Object Modeling Catalog - FUNCTIONAL") 
    print("✅ Epic 3: Relationship Mapping & NOM - FUNCTIONAL")

if __name__ == "__main__":
    main()
