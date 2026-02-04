import pytest
import ray
from ray import serve
import httpx





BASE_URL = "http://127.0.0.1:8000/embed"







# -------------------------
# Helper Client
# -------------------------
@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL)


# -------------------------
# Dense Query Test
# -------------------------
def test_dense_query(client):
    payload = {"text": ["hello world"]}

    response = client.post("/dense/query", json=payload)

    assert response.status_code == 200
    assert response.json() is not None


# -------------------------
# Dense Text Test
# -------------------------
def test_dense_text(client):
    payload = {"text": ["hello world"]}

    response = client.post("/dense/text", json=payload)

    assert response.status_code == 200


# -------------------------
# Sparse BM25 Test
# -------------------------
def test_sparse_bm25(client):
    payload = {"text": ["hello world"]}

    response = client.post("/sparse/bm25", json=payload)

    assert response.status_code == 200


# -------------------------
# Sparse SPLADE Test
# -------------------------
def test_sparse_splade(client):
    payload = {"text": ["hello world"]}

    response = client.post("/sparse/splade", json=payload)

    assert response.status_code == 200


# -------------------------
# Sparse TFIDF Test
# -------------------------
def test_sparse_tfidf(client):
    payload = {"text": ["hello world"]}

    response = client.post("/sparse/tfidf", json=payload)

    assert response.status_code == 200
