# tested
import requests

def test_delete_by_json(ray_serve_app, insert_default_documents):
    """Test delete by JSON field in default collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    filenames_to_delete = ["greeting", "example", "lorem"]
    params = [("filename", fn) for fn in filenames_to_delete]
    
    response = requests.delete(f"{base_url}/delete_by_json", params=params, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "documents_v1"
    print(data)
    assert data["total_delete_count"] == 3
    assert len(data["files"]) == len(filenames_to_delete)


def test_delete_by_json_named_collection(ray_serve_app, insert_named_documents):
    """Test delete by JSON field in named collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    filenames_to_delete = ["greeting", "example", "lorem"]
    params = [("filename", fn) for fn in filenames_to_delete]
    
    response = requests.delete(f"{base_url}/delete_by_json/dear", params=params, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["collection_name"] == "dear"
    assert data["total_delete_count"] == 3


def test_delete_by_ids_default_collection(ray_serve_app, insert_default_documents):
    """Test delete by IDs in default collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    ids_to_delete = insert_default_documents["ids"]
    params = [("ids", id) for id in ids_to_delete]
    
    response = requests.delete(f"{base_url}/delete_by_ids", params=params, headers=headers)
    
    assert response.status_code == 200
    assert response.json() == True


def test_delete_by_ids_named_collection(ray_serve_app, insert_named_documents):
    """Test delete by IDs in named collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}
    
    ids_to_delete = insert_named_documents["ids"]
    params = [("ids", id) for id in ids_to_delete]
    
    response = requests.delete(f"{base_url}/delete_by_ids/dear", params=params, headers=headers)
    
    assert response.status_code == 200
    assert response.json() == True