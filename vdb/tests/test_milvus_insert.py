
import requests

def test_document_insertion_collection(ray_serve_app, create_both_collections, sample_documents):
    """Test inserting documents into default collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.post(f"{base_url}/insert_documents", json=sample_documents, headers=headers)
    
    assert response.status_code == 200 
    data = response.json()
    assert data["insert_count"] == 3
    assert len(data["ids"]) == 3


def test_document_insertion_named_collection(milvus_empty_collections, sample_documents):
    """Test inserting documents into named collection"""
    base_url = milvus_empty_collections["base_url"]
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.post(f"{base_url}/insert_documents/dear", json=sample_documents, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["insert_count"] == 3







