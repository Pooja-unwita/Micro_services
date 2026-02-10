# test completed
import requests

def test_dense_search_collection(ray_serve_app, insert_default_documents):
    """Test dense vector search in default collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    payload = {
        "dense_vector": [[0.1]*1024],
        "sparse_vector": None,
        "top_k": 3,
        "filter_expr": None
    }
    
    response = requests.post(f"{base_url}/search", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "documents_v1"
    assert len(data["chunks"]) == 1
    assert len(data["chunks"][0]) == 3
    
    REQUIRED_KEYS = {"id", "distance", "filename", "chunks"}
    for chunk in data["chunks"][0]:
        assert REQUIRED_KEYS.issubset(chunk.keys())


def test_dense_search_named_collection(ray_serve_app, insert_named_documents):
    """Test dense search in named collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    payload = {
        "dense_vector": [[0.1]*1024],
        "sparse_vector": None,
        "top_k": 3,
        "filter_expr": None
    }
    
    response = requests.post(f"{base_url}/search/dear", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "dear"
    assert len(data["chunks"][0]) <= 3


