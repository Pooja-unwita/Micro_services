import requests

def test_milvus_create_hybrid_collection(ray_serve_app_hybrid, cleanup_collections):
    """Test creating default collection"""
    base_url = ray_serve_app_hybrid
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.post(f"{base_url}/create_collection", json={}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "documents_v1"
    assert data["status"] == "created"

def test_document_insertion_into_hybrid_with_sparse(milvus_empty_hybrid_collections, sample_hybrid_documents):
    """Test inserting hybrid documents into hybrid collection"""
    base_url = milvus_empty_hybrid_collections["base_url"]
    headers = {"Authorization": "Bearer fake_token"}
  
    response = requests.post(f"{base_url}/insert_documents/dear", json=sample_hybrid_documents, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["insert_count"] == 3
    assert len(data["ids"]) == 3

