# tested
import requests


def test_milvus_create_collection(ray_serve_app, cleanup_collections):
    """Test creating default collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.post(f"{base_url}/create_collection", json={}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "documents_v1"
    assert data["status"] == "created"


def test_milvus_collection_exist_verification(ray_serve_app, create_default_collection):
    """Test verifying existing collection returns 'verified' status"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}

    response = requests.post(f"{base_url}/create_collection", json={}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "documents_v1"
    assert data["status"] == "verified"


def test_milvus_create_named_collection(ray_serve_app, cleanup_collections):
    """Test creating named collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.post(f"{base_url}/create_collection/dear", json={}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "dear"
    assert data["status"] == "created"


def test_milvus_create_named_collection_verification(ray_serve_app, create_named_collection):
    """Test verifying existing named collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.post(f"{base_url}/create_collection/dear", json={}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "dear"
    assert data["status"] == "verified"



def test_drop_collection(ray_serve_app, create_default_collection):
    """Test dropping default collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.delete(f"{base_url}/drop_collection", json={}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "documents_v1"
    assert data["drop_status"] == True


def test_drop_named_collection(ray_serve_app, create_named_collection):
    """Test dropping named collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.delete(f"{base_url}/drop_collection/dear", json={}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "dear"
    assert data["drop_status"] == True




