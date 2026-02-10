import pytest
from ray import serve   
import ray
import time
import requests
from Embedding_Service.embedding_service import app_builder
from Embedding_Service.routers.routers import app
from fastapi.testclient import TestClient



@pytest.fixture(scope="module")
def sample_args():
    return {
        "tei_url": "http://localhost:8080",
        "tei_flag": False,
        "custom_flag": True,
        "custom_embed_model": "all-MiniLM-L6-v2",
        "query_annotation": "query: ",
        "device": "cpu",
        "concurrency": 1,
        "splade_model_name": "naver/splade-cocondenser-ensemblev2",
        "tfidf_max_features": 1000,
        "splade_device": "cpu"
    }

@pytest.fixture(scope="module")
def ray_serve_app(sample_args):
    """Start Ray Serve with the embedding service"""
    # Initialize Ray if not already initialized
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    # Start Serve
    serve.start(detached=True, http_options={"host": "127.0.0.1", "port": 8001})
    
    # Build and deploy the app
    embedding_app = app_builder(sample_args)
    serve.run(embedding_app, name="Embedding_Service", route_prefix="/embed")
    
    # Wait for deployment to be ready
    time.sleep(5)
    
    yield
    
    # Cleanup
    serve.shutdown()
    ray.shutdown()


@pytest.fixture(scope="module")
def base_url():
    """Base URL for the service"""
    return "http://localhost:8001/embed"


# -------------------------
# Dense Query Endpoint Tests
# -------------------------
def test_dense_query_single_text(ray_serve_app, base_url):
    """Test dense query endpoint with single text"""
    payload = {"text": ["hello world"]}
    
    response = requests.post(f"{base_url}/dense/query", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "embeddings" in data or isinstance(data, list)
    assert len(data) > 0


# # -------------------------
# # Dense Text Test
# # -------------------------
# def test_dense_text(client):
#     payload = {"text": ["hello world"]}

#     response = client.post("/dense/text", json=payload)

#     assert response.status_code == 200


# # -------------------------
# # Sparse BM25 Test
# # -------------------------
# def test_sparse_bm25(client):
#     payload = {"text": ["hello world"]}

#     response = client.post("/sparse/bm25", json=payload)

#     assert response.status_code == 200


# # -------------------------
# # Sparse SPLADE Test
# # -------------------------
# def test_sparse_splade(client):
#     payload = {"text": ["hello world"]}

#     response = client.post("/sparse/splade", json=payload)

#     assert response.status_code == 200


# # -------------------------
# # Sparse TFIDF Test
# # -------------------------
# def test_sparse_tfidf(client):
#     payload = {"text": ["hello world"]}

#     response = client.post("/sparse/tfidf", json=payload)

#     assert response.status_code == 200
