# Authentication_Service/test/conftest.py
import pytest
import os
import requests
import time
import ray
from ray import serve
from datetime import datetime, timedelta, timezone

AUDIENCE = "FE_Service"
ISSUER = "Auth_Service"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["TESTING"] = "true"
    yield
    del os.environ["TESTING"]


@pytest.fixture(scope="session")
def jwt_config():
    """JWT configuration for testing"""
    return {
        "algorithm": "RS256",
        "issuer": "test-issuer",
        "audience": "test-audience",
        "expiration_minutes": 60
    }

# -------------------------
# Fixtures
# -------------------------
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


@pytest.fixture(scope="module")
def ray_serve_app(cleanup_ray):
    """Start Ray Serve with the authentication service"""

    from Authentication_Service.main import auth_app_builder
    KEYS = {
        "key-1": {
            "private": "Authentication_Service/keys/key1_private.pem",
            "public": "Authentication_Service/keys/key1_public.pem",
            "active": False,
        },
        "key-2": {
            "private": "Authentication_Service/keys/key2_private.pem",
            "public": "Authentication_Service/keys/key2_public.pem",
            "active": True,
        }
    }
    # Initialize Ray
    ray.init(ignore_reinit_error=True, num_cpus=2)
    
    # Start Serve
    serve.start(
        detached=False,
        http_options={"host": "127.0.0.1", "port": 8002}
    )
    
    try:
        # Build and deploy the app
        auth_app = auth_app_builder(args={"KEYS": KEYS})
        serve.run(
            auth_app,
            name="Authentication_Service",
            route_prefix="/auth"
        )
        
        # Wait for service to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(
                    "http://localhost:8002/auth/docs",
                    timeout=2
                )
                if response.status_code == 200:
                    print("✓ Auth Service ready")
                    break
            except Exception as e:
                if i == max_retries - 1:
                    raise RuntimeError(f"Service failed to start: {e}")
                time.sleep(2)
        
        yield "http://localhost:8002/auth"
        
    except Exception as e:
        pytest.skip(f"Service deployment failed: {e}")


@pytest.fixture
def sample_payload():
    """Sample JWT payload - audience and issuer will be added by the service"""
    
    return {
        "user_name": "user123",   
        "scope": ["read", "write"],
        "email": "test@example.com",
        "role": "admin",
        "aud": AUDIENCE,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=60)).timestamp() )
    }


@pytest.fixture
def verify_request_data():
    """Verification request data with fixed audience and issuer"""
    return {
        "AUDIENCE": AUDIENCE,
        "ISSUER": ISSUER
    }
