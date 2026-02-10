
import pytest
import ray
from ray import serve
import requests
import time
import json

@pytest.fixture(scope="module")
def milvus_hybrid_config_new():
    """
    Realistic Milvus configuration fixture.
    Matches production YAML structure.
    """
    return {"milvus_config":{
        "host": "localhost",
        "port": 19530,
        "database": "default",
        "collection_name": "documents_v1",
        "metric_type": "COSINE",
        "top_k": 5,
        "output_fields": ["chunks", "metadata"],
        "ann_field": "vectors",
        "deletion_field_name": "metadata",
        "Schema": {
            "fields": [
                {
                    "name": "id",
                    "dtype": "INT64",
                    "is_primary": True,
                    "auto_id": True,
                },
                {
                    "name": "chunks",
                    "dtype": "VARCHAR",
                    "max_length": 65535,
                },
                {
                    "name": "vectors",
                    "dtype": "FLOAT_VECTOR",
                    "dim": 1024,
                },
                {
                    "name": "metadata",
                    "dtype": "JSON",
                },
            ]
        },
        "function": {
            "name": "bm25",
            "input_field_names": ["chunks"],
            "output_field_names": ["sparse_vectors_BM25"],
        },
        "Hybrid_search": {
            "Hybrid_search_flag": True,
            "annn_fields": ["vectors", "sparse_vectors_BM25"],
            "Hybrid_schema": {
                "fields": [
                    {
                        "name": "id",
                        "dtype": "INT64",
                        "is_primary": True,
                        "auto_id": True,
                    },
                    {
                        "name": "chunks",
                        "dtype": "VARCHAR",
                        "max_length": 65535,
                    },
                    {
                        "name": "vectors",
                        "dtype": "FLOAT_VECTOR",
                        "dim": 1024,
                    },
                    {
                        "name": "metadata",
                        "dtype": "JSON",
                    },
                    {
                        "name": "sparse_vectors_BM25",
                        "dtype": "SPARSE_FLOAT_VECTOR",
                    },
                ]
            },
        },
        "indexes": {
            "Dense_index": [
                {
                    "index_type": "IVF_FLAT",
                    "index_params": {"nlist": 500},
                    "search_params": {
                        "params": {"nprobe": 50},
                        "metric_type": "COSINE",
                    },
                },
                {
                    "index_type": "HNSW",
                    "index_params": {"M": 30, "efConstruction": 360},
                    "search_params": {
                        "params": {"ef": 50},
                        "metric_type": "COSINE",
                    },
                },
            ],
            "Sparse_index": [
                {
                    "index_type": "SPARSE_INVERTED_INDEX",
                    "index_params": {
                        "inverted_index_algo": "DAAT_MAXSCORE"
                    },
                    "search_params": {
                        "params": {"drop_ratio_search": 0.2},
                        "metric_type": "IP",
                    },
                }
            ],
        },
    }
    }


def _get_base_milvus_config():
    """Base Milvus configuration - regular function, not a fixture"""
    return {"milvus_config":{
        "host": "localhost",
        "port": 19530,
        "database": "default",
        "collection_name": "documents_v1",
        "metric_type": "COSINE",
        "top_k": 5,
        "output_fields": ["chunks", "metadata"],
        "ann_field": "vectors",
        "deletion_field_name": "metadata",
        "Schema": {
            "fields": [
                {"name": "id", "dtype": "INT64", "is_primary": True, "auto_id": True},
                {"name": "chunks", "dtype": "VARCHAR", "max_length": 65535},
                {"name": "vectors", "dtype": "FLOAT_VECTOR", "dim": 1024},
                {"name": "metadata", "dtype": "JSON"},
            ]
        },
        "function": {
            "name": "bm25",
            "input_field_names": ["chunks"],
            "output_field_names": ["sparse_vectors_BM25"],
        },
        "Hybrid_search": {
            "Hybrid_search_flag": True,
            "annn_fields": ["vectors", "sparse_vectors_BM25"],
            "Hybrid_schema": {
                "fields": [
                    {"name": "id", "dtype": "INT64", "is_primary": True, "auto_id": True},
                    {"name": "chunks", "dtype": "VARCHAR", "max_length": 65535},
                    {"name": "vectors", "dtype": "FLOAT_VECTOR", "dim": 1024},
                    {"name": "metadata", "dtype": "JSON"},
                    {"name": "sparse_vectors_BM25", "dtype": "SPARSE_FLOAT_VECTOR"},
                ]
            },
        },
        "indexes": {
            "Dense_index": [{
                "index_type": "HNSW",
                "index_params": {"M": 30, "efConstruction": 360},
                "search_params": {"params": {"ef": 50}, "metric_type": "COSINE"},
            }],
            "Sparse_index": [{
                "index_type": "SPARSE_INVERTED_INDEX",
                "index_params": {"inverted_index_algo": "DAAT_MAXSCORE"},
                "search_params": {"params": {"drop_ratio_search": 0.2}, "metric_type": "IP"},
            }]
        },
    }}


@pytest.fixture(scope="module")
def milvus_config():
    """Standard Milvus configuration with Hybrid_search_flag=False"""
    return _get_base_milvus_config()


@pytest.fixture(scope="module")
def milvus_hybrid_config():
    """Hybrid Milvus configuration with Hybrid_search_flag=True"""
    config = _get_base_milvus_config()  
    config["milvus_config"]["Hybrid_search"]["Hybrid_search_flag"] = True
    return config


@pytest.fixture(scope="module")
def milvus_config_error_cases():
    """Error case config with metadata as VARCHAR instead of JSON"""
    config = _get_base_milvus_config()  
    config["milvus_config"]["Schema"]["fields"][3] = {
        "name": "metadata",
        "dtype": "VARCHAR",
        "max_length": 65500,
    }
    config["milvus_config"]["Hybrid_search"]["Hybrid_search_flag"] = True
    return config


@pytest.fixture(scope="module", autouse=True)
def cleanup_ray():
    """Ensure Ray is cleaned up before and after tests"""
    try:
        serve.shutdown()
        ray.shutdown()
    except:
        pass
    
    yield
    
    try:
        serve.shutdown()
        ray.shutdown()
    except:
        pass


def _start_ray_serve(config, port=8002):
    """Helper to start Ray Serve with given config"""
    from vdb.main import milvus_service_builder
    import os
    
    os.environ["TESTING_MODE"] = "true"
    
    try:
        ray.init(ignore_reinit_error=True, num_cpus=2)
        serve.start(detached=False, http_options={"host": "127.0.0.1", "port": port})
        
        auth_app = milvus_service_builder(args=config)
        serve.run(auth_app, name="Vector DataBase Service", route_prefix="/milvus")
        
        # Wait for service readiness
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"http://localhost:{port}/milvus/docs", timeout=2)
                if response.status_code == 200:
                    print(f"Vector DB Service ready on port {port}")
                    return f"http://localhost:{port}/milvus"
            except Exception as e:
                if i == max_retries - 1:
                    raise RuntimeError(f"Service failed to start: {e}")
                time.sleep(2)
    except Exception:
        os.environ.pop("TESTING_MODE", None)
        raise


@pytest.fixture(scope="module")
def ray_serve_app(cleanup_ray, milvus_config):
    """Standard Ray Serve app (Hybrid_search_flag=False)"""
    base_url = _start_ray_serve(milvus_config)
    yield base_url
    
    import os
    os.environ.pop("TESTING_MODE", None)
    serve.shutdown()
    ray.shutdown()


@pytest.fixture(scope="module")
def ray_serve_app_hybrid(cleanup_ray, milvus_hybrid_config_new):
    """Hybrid Ray Serve app (Hybrid_search_flag=True)"""
    x=milvus_hybrid_config_new
    print(x)
    base_url = _start_ray_serve(milvus_hybrid_config_new)
    yield base_url
    
    import os
    os.environ.pop("TESTING_MODE", None)
    serve.shutdown()
    ray.shutdown()


@pytest.fixture(scope="module")
def ray_serve_app_error_cases(cleanup_ray, milvus_config_error_cases):
    """Error case Ray Serve app (VARCHAR metadata)"""
    base_url = _start_ray_serve(milvus_config_error_cases)
    yield base_url
    
    import os
    os.environ.pop("TESTING_MODE", None)
    serve.shutdown()
    ray.shutdown()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration shared across all tests"""
    return {
        "default_collection": "documents_v1", 
        "named_collection": "dear",
    }


@pytest.fixture(scope="function")
def sample_documents():
    """Sample documents with metadata as JSON string"""
    return [
        {
            "chunks": "hello world",
            "vectors": [0.1] * 1024,
            "metadata": {"filename": "greeting", "source": "unit_test"}
        },
        {
            "chunks": "foo bar",
            "vectors": [0.2] * 1024,
            "metadata": {"filename": "example", "source": "unit_test"}
        },
        {
            "chunks": "lorem ipsum",
            "vectors": [0.3] * 1024,
            "metadata": {"filename": "lorem", "source": "unit_test", "pgnumber": 1}
        }
    ]


@pytest.fixture(scope="function")
def sample_hybrid_documents():
    """Sample documents with sparse vectors for hybrid search"""
    return [
        {
            "chunks": "hello world",
            "vectors": [0.1] * 1024,
            "metadata": {"filename": "greeting", "source": "unit_test"},
            "sparse_vectors_BM25": {0: 1.0, 3: 0.5}
        },
        {
            "chunks": "foo bar",
            "vectors": [0.2] * 1024,
            "metadata": {"filename": "example", "source": "unit_test"},
            "sparse_vectors_BM25": {1: 0.8, 4: 0.3}
        },
        {
            "chunks": "lorem ipsum",
            "vectors": [0.3] * 1024,
            "metadata": {"filename": "lorem", "source": "unit_test", "pgnumber": 1},
            "sparse_vectors_BM25": {2: 0.9, 5: 0.7}
        }
    ]


@pytest.fixture(scope="function")
def cleanup_collections(ray_serve_app, test_config):
    """Drop collections before each test - CRITICAL for test isolation"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}

    for collection in ["", f"/{test_config['named_collection']}"]:
        try:
            requests.delete(f"{base_url}/drop_collection{collection}", json={}, headers=headers)
        except:
            pass  
    
    yield
    


@pytest.fixture(scope="function")
def create_default_collection(ray_serve_app, cleanup_collections):
    """Create default collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}

    response = requests.post(f"{base_url}/create_collection", json={}, headers=headers)
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="function")
def create_named_collection(ray_serve_app, test_config, cleanup_collections):
    """Create named collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}

    response = requests.post(
        f"{base_url}/create_collection/{test_config['named_collection']}", 
        json={}, 
        headers=headers
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="function")
def create_both_collections(create_default_collection, create_named_collection):
    """Create both collections"""
    return {
        "default": create_default_collection,
        "named": create_named_collection
    }


@pytest.fixture(scope="function")
def insert_default_documents(ray_serve_app, create_default_collection, sample_documents):
    """Insert documents into default collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}

    response = requests.post(f"{base_url}/insert_documents", json=sample_documents, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    return {
        "ids": data.get("ids", []),
        "count": len(data.get("ids", [])),
        "documents": sample_documents
    }


@pytest.fixture(scope="function")
def insert_named_documents(ray_serve_app, test_config, create_named_collection, sample_documents):
    """Insert documents into named collection"""
    base_url = ray_serve_app
    headers = {"Authorization": "Bearer fake_token"}

    response = requests.post(
        f"{base_url}/insert_documents/{test_config['named_collection']}",
        json=sample_documents,
        headers=headers
    )
    assert response.status_code == 200
    
    data = response.json()
    return {
        "ids": data.get("ids", []),
        "count": len(data.get("ids", [])),
        "documents": sample_documents
    }


@pytest.fixture(scope="function")
def insert_both_documents(insert_default_documents, insert_named_documents):
    """Insert documents into both collections"""
    return {
        "default": insert_default_documents,
        "named": insert_named_documents
    }



@pytest.fixture(scope="function")
def milvus_empty_collections(ray_serve_app, test_config, create_both_collections):
    """Empty collections ready for insertion"""
    return {
        "base_url": ray_serve_app,
        "config": test_config,
        "collections": create_both_collections
    }


@pytest.fixture(scope="function")
def milvus_empty_hybrid_collections(ray_serve_app_hybrid, test_config, create_both_collections):
    """Empty hybrid collections"""
    return {
        "base_url": ray_serve_app_hybrid,
        "config": test_config,
        "collections": create_both_collections
    }


@pytest.fixture(scope="function")
def milvus_full_setup(ray_serve_app, test_config, insert_both_documents):
    """Complete setup with data"""
    return {
        "base_url": ray_serve_app,
        "config": test_config,
        "data": insert_both_documents
    }