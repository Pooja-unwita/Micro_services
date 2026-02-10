import requests
# tested - partially- hybrid search concept has to be handled
def test_milvus_create_collection_error(ray_serve_app_error_cases):
    """Test 500 error when creating collection fails"""
    base_url = ray_serve_app_error_cases
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.post(f"{base_url}/create_collection", json={}, headers=headers)
    
    assert response.status_code in [200, 500]
    if response.status_code == 500:
        assert "Milvus failure" in response.text


def test_milvus_create_named_collection_invalid_name_error(ray_serve_app):
    """Test invalid collection name error"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.post(f"{base_url}/create_collection/10dear", json={}, headers=headers)
    
    assert response.status_code in [400, 500]
    assert "naming rules" in response.text.lower()


def test_drop_unavailable_named_collection(ray_serve_app, cleanup_collections):
    """Test dropping nonexistent collection returns 404"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.delete(f"{base_url}/drop_collection/documents_v10", json={}, headers=headers)
    
    assert response.status_code == 404
    assert "Collection not found" in response.text


def test_dense_search_unavailable_named_collection(ray_serve_app, cleanup_collections):
    """Test searching nonexistent collection returns 404"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    payload = {
        "dense_vector": [[0.1]*1024],
        "sparse_vector": None,
        "top_k": 3,
        "filter_expr": None
    }
    
    response = requests.post(f"{base_url}/search/dear10", json=payload, headers=headers)
    
    assert response.status_code == 404
    assert "Collection not found" in response.text


def test_hybrid_search_named_collection_no_sparse_error(ray_serve_app_hybrid,cleanup_collections,create_named_collection):
    """Test 400 when hybrid search enabled but no sparse vector"""
    base_url = ray_serve_app_hybrid
    headers = {"Authorization": "Bearer fake_token"}
    
    payload = {
        "dense_vector": [[0.1]*1024],
        "sparse_vector": None,
        "top_k": 3,
        "filter_expr": None
    }
    
    response = requests.post(f"{base_url}/search/dear", json=payload, headers=headers)
    
    assert response.status_code == 400
    assert "sparse_vector is not provided" in response.text


def test_delete_by_json_unavailable_collection(ray_serve_app, cleanup_collections):
    """Test 404 when deleting from nonexistent collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    filenames_to_delete = ["lorem", "example"]
    params = [("filename", fn) for fn in filenames_to_delete]
    
    response = requests.delete(f"{base_url}/delete_by_json/dummy", params=params, headers=headers)
    
    assert response.status_code == 404
    assert "Collection not found" in response.text


def test_delete_by_ids_unavailable_collection(ray_serve_app, cleanup_collections):
    """Test 404 when deleting from nonexistent collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    params = [("ids", 1), ("ids", 2)]
    
    response = requests.delete(f"{base_url}/delete_by_ids/dummy", params=params, headers=headers)
    
    assert response.status_code == 404
    assert "Collection not found" in response.text


def test_document_insertion_unavailable_named_collection(milvus_empty_collections, sample_documents):
    """Test 404 when inserting into nonexistent collection"""
    base_url = milvus_empty_collections["base_url"]
    headers = {"Authorization": "Bearer fake_token"}
    
    response = requests.post(f"{base_url}/insert_documents/dummy", json=sample_documents, headers=headers)
    
    assert response.status_code == 404
    assert "Collection not found" in response.text


def test_document_insertion_without_schema_match(milvus_empty_collections):
    """Test 400 when document schema doesn't match"""
    base_url = milvus_empty_collections["base_url"]
    headers = {"Authorization": "Bearer fake_token"}
    
    invalid_documents = [
        {
            "wrong_field": "test",
            "bad_vectors": [0.1] * 1024,
            "invalid_metadata": {"filename": "test"}
        }
    ]
    
    response = requests.post(f"{base_url}/insert_documents/dear", json=invalid_documents, headers=headers)
    
    assert response.status_code in [400, 502]
    assert "schema" in response.text.lower()


def test_document_insertion_into_hybrid_without_sparse(milvus_empty_hybrid_collections, sample_documents):
    """Test inserting non-hybrid documents into hybrid collection"""
    base_url = milvus_empty_hybrid_collections["base_url"]
    headers = {"Authorization": "Bearer fake_token"}
  
    response = requests.post(f"{base_url}/insert_documents/dear", json=sample_documents, headers=headers)
    
    assert response.status_code == 400



def test_dense_search_named_collection_sparse_given_error(ray_serve_app, insert_named_documents):
    """Test 401 when hybrid disabled but sparse vector provided"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    payload = {
        "dense_vector": [[0.1]*1024],
        "sparse_vector": [{0: 1.0}],
        "top_k": 3,
        "filter_expr": None
    }
    
    response = requests.post(f"{base_url}/search/dear", json=payload, headers=headers)
    
    assert response.status_code == 401
    assert "Hybrid search is disabled but sparse_vector was provided" in response.text
