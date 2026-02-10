import pytest


import requests
import jwt

from unittest.mock import Mock
from datetime import datetime, timedelta, timezone


# -------------------------
# Constants
# -------------------------
AUDIENCE = "FE_Service"
ISSUER = "Auth_Service"




# -------------------------
# Token Issuance Tests (UNCHANGED)
# -------------------------
def test_issue_access_token_success(ray_serve_app, sample_payload):
    """Test successful token issuance"""
    base_url = ray_serve_app
    
    response = requests.post(
        f"{base_url}/token",
        json=sample_payload
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_issue_token_with_minimal_payload(ray_serve_app):
    """Test token issuance with minimal payload"""
    base_url = ray_serve_app
    minimal_payload = {
        "user_name": "user456",
        "aud": AUDIENCE,
        "scope": ["read"]
    }
    
    response = requests.post(
        f"{base_url}/token",
        json=minimal_payload
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_issue_token_empty_payload(ray_serve_app):
    """Test token issuance with empty payload"""
    base_url = ray_serve_app
    
    response = requests.post(
        f"{base_url}/token",
        json={}
    )
    
    # Should return validation error
    assert response.status_code == 422


def test_issue_token_invalid_json(ray_serve_app):
    """Test token issuance with invalid JSON"""
    base_url = ray_serve_app
    
    response = requests.post(
        f"{base_url}/token",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422


# -------------------------
# Token Verification Tests (UPDATED)
# -------------------------
def test_verify_token_success(ray_serve_app, sample_payload, verify_request_data):
    """Test successful token verification with correct audience and issuer"""
    base_url = ray_serve_app
    
    # First, issue a token
    token_response = requests.post(
        f"{base_url}/token",
        json=sample_payload
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    
    # Then verify it with correct audience and issuer
    response = requests.post(
        f"{base_url}/verify-token",
        json=verify_request_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    payload = response.json()
    assert "user_name" in payload
    assert payload["user_name"] == sample_payload["user_name"]
    assert "email" in payload
    assert payload["email"] == sample_payload["email"]
    assert "role" in payload        
    assert payload["role"] == sample_payload["role"]
    # Verify the token has correct audience and issuer
    assert payload.get("aud") == AUDIENCE
    assert payload.get("iss") == ISSUER


def test_verify_token_missing_authorization_header(ray_serve_app, verify_request_data):
    """Test verification without authorization header"""
    base_url = ray_serve_app
    
    response = requests.post(
        f"{base_url}/verify-token",
        json=verify_request_data
    )
    
    assert response.status_code == 401  # Forbidden without auth header


def test_verify_token_invalid_bearer_format(ray_serve_app, verify_request_data):
    """Test verification with invalid bearer format"""
    base_url = ray_serve_app
    
    response = requests.post(
        f"{base_url}/verify-token",
        json=verify_request_data,
        headers={"Authorization": "InvalidFormat token123"}
    )
    
    assert response.status_code == 401
    # Due to FastAPI's HTTPBearer, the error message is standardized
    assert "Not authenticated" in response.json()["detail"]


def test_verify_token_malformed_token(ray_serve_app, verify_request_data):
    """Test verification with malformed token"""
    base_url = ray_serve_app
    
    response = requests.post(
        f"{base_url}/verify-token",
        json=verify_request_data,
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]



def test_verify_token_expired(ray_serve_app, verify_request_data):
    """Test verification with expired token"""
    base_url = ray_serve_app
  
    # Create payload with past expiration
    expired_payload = {
        "user_name": "user123",
        "scope": ["read", "write"],
        "aud": AUDIENCE,
        "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
    }
    
    # Issue token
    token_response = requests.post(
        f"{base_url}/token",
        json=expired_payload
    )
    token = token_response.json()["access_token"]
    
    # Try to verify expired token
    response = requests.post(
        f"{base_url}/verify-token",
        json=verify_request_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


# -------------------------
# UPDATED: Audience/Issuer Tests
# -------------------------
def test_verify_token_wrong_audience(ray_serve_app, sample_payload):
    """Test verification with WRONG audience - should FAIL"""
    base_url = ray_serve_app
    
    # Issue token
    token_response = requests.post(
        f"{base_url}/token",
        json=sample_payload
    )
    token = token_response.json()["access_token"]
    
    # Verify with WRONG audience
    wrong_audience_request = {
        "AUDIENCE": "WrongService",  # Not FE_Service
        "ISSUER": ISSUER
    }
    
    response = requests.post(
        f"{base_url}/verify-token",
        json=wrong_audience_request,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should FAIL verification
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"] 
    # or "verification failed" in response.json()["detail"].lower()


def test_verify_token_wrong_issuer(ray_serve_app, sample_payload):
    """Test verification with WRONG issuer - should FAIL"""
    base_url = ray_serve_app
    
    # Issue token
    token_response = requests.post(
        f"{base_url}/token",
        json=sample_payload
    )
    token = token_response.json()["access_token"]
    
    # Verify with WRONG issuer
    wrong_issuer_request = {
        "AUDIENCE": AUDIENCE,
        "ISSUER": "WrongAuthService"  # Not Auth_Service
    }
    
    response = requests.post(
        f"{base_url}/verify-token",
        json=wrong_issuer_request,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should FAIL verification
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"] 
    # or "verification failed" in response.json()["detail"].lower()


def test_verify_token_both_wrong(ray_serve_app, sample_payload):
    """Test verification with BOTH wrong audience AND issuer - should FAIL"""
    base_url = ray_serve_app
    
    # Issue token
    token_response = requests.post(
        f"{base_url}/token",
        json=sample_payload
    )
    token = token_response.json()["access_token"]
    
    # Verify with both wrong
    both_wrong_request = {
        "AUDIENCE": "WrongService",
        "ISSUER": "WrongAuthService"
    }
    
    response = requests.post(
        f"{base_url}/verify-token",
        json=both_wrong_request,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should FAIL verification
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


def test_verify_token_missing_audience_in_request(ray_serve_app, sample_payload):
    """Test verification when AUDIENCE is missing from request - should FAIL"""
    base_url = ray_serve_app
    
    # Issue token
    token_response = requests.post(
        f"{base_url}/token",
        json=sample_payload
    )
    token = token_response.json()["access_token"]
    
    # Verify without audience
    missing_audience_request = {
        "ISSUER": ISSUER
        # AUDIENCE is missing
    }
    
    response = requests.post(
        f"{base_url}/verify-token",
        json=missing_audience_request,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should return validation error
    assert response.status_code == 422


def test_verify_token_missing_issuer_in_request(ray_serve_app, sample_payload):
    """Test verification when ISSUER is missing from request - should FAIL"""
    base_url = ray_serve_app
    
    # Issue token
    token_response = requests.post(
        f"{base_url}/token",
        json=sample_payload
    )
    token = token_response.json()["access_token"]
    
    # Verify without issuer
    missing_issuer_request = {
        "AUDIENCE": AUDIENCE
        # ISSUER is missing
    }
    
    response = requests.post(
        f"{base_url}/verify-token",
        json=missing_issuer_request,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should return validation error
    assert response.status_code == 422


def test_verify_token_missing_request_body(ray_serve_app, sample_payload):
    """Test verification without request body - should FAIL"""
    base_url = ray_serve_app
    
    # Issue token
    token_response = requests.post(
        f"{base_url}/token",
        json=sample_payload
    )
    token = token_response.json()["access_token"]
    
    # Verify without body
    response = requests.post(
        f"{base_url}/verify-token",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422  # Validation error


# -------------------------
# Integration Tests (UPDATED)
# -------------------------
def test_full_token_lifecycle(ray_serve_app, verify_request_data):
    """Test complete token lifecycle: issue -> verify -> check claims"""
    base_url = ray_serve_app
    
    # Step 1: Issue token
    payload = {
        "user_name": "integration_test_user",
        "email": "integration@test.com",
        "scope": ["read", "write"],
        "role": "tester",
        "aud": AUDIENCE
    }
    
    issue_response = requests.post(
        f"{base_url}/token",
        json=payload
    )
    assert issue_response.status_code == 200
    token = issue_response.json()["access_token"]
    
    # Step 2: Verify token with correct audience and issuer
    verify_response = requests.post(
        f"{base_url}/verify-token",
        json=verify_request_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert verify_response.status_code == 200
    verified_payload = verify_response.json()
    
    # Step 3: Check payload matches AND has correct audience/issuer
    assert verified_payload["user_name"] == payload["user_name"]
    assert verified_payload["email"] == payload["email"]
    assert verified_payload["role"] == payload["role"]
    assert verified_payload.get("aud") == payload["aud"]
    assert verified_payload.get("iss") == ISSUER


def test_multiple_tokens_different_users(ray_serve_app, verify_request_data):
    """Test issuing and verifying multiple tokens for different users"""
    base_url = ray_serve_app
    
    users = [
        {"user_name": "user1", "role": "admin", "aud": AUDIENCE, "scope": ["read", "write"]},
        {"user_name": "user2", "role": "user", "aud": AUDIENCE, "scope": ["read"]},
        {"user_name": "user3", "role": "guest", "aud": AUDIENCE, "scope": ["read"]}
    ]
    
    tokens = []
    
    # Issue tokens for all users
    for user in users:
        response = requests.post(f"{base_url}/token", json=user)
        assert response.status_code == 200
        tokens.append(response.json()["access_token"])
    
    # Verify all tokens with correct audience and issuer
    for i, token in enumerate(tokens):
        verify_response = requests.post(
            f"{base_url}/verify-token",
            json=verify_request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert verify_response.status_code == 200
        verified = verify_response.json()
        assert verified["user_name"] == users[i]["user_name"]
        assert verified.get("aud") == users[i]["aud"]
        assert verified.get("iss") == ISSUER


def test_concurrent_token_issuance(ray_serve_app):
    """Test concurrent token issuance"""
    import concurrent.futures
    base_url = ray_serve_app
    
    def issue_token(user_id):
        payload = {"user_name": f"user_{user_id}", "aud": AUDIENCE, "scope": ["read"]}
        response = requests.post(f"{base_url}/token", json=payload)
        return response.status_code == 200
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(issue_token, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    assert all(results), "Some token issuances failed"


# -------------------------
# Security Tests (UPDATED)
# -------------------------
def test_token_cannot_be_modified(ray_serve_app, sample_payload, verify_request_data):
    """Test that modified tokens are rejected"""
    base_url = ray_serve_app
    
    # Issue token
    token_response = requests.post(f"{base_url}/token", json=sample_payload)
    token = token_response.json()["access_token"]
    
    # Modify token (corrupt it)
    parts = token.split('.')
    if len(parts) == 3:
        # Change one character in the payload
        modified_token = parts[0] + '.' + parts[1][:-1] + 'X.' + parts[2]
        
        # Try to verify modified token
        verify_response = requests.post(
            f"{base_url}/verify-token",
            json=verify_request_data,
            headers={"Authorization": f"Bearer {modified_token}"}
        )
        
        assert verify_response.status_code == 401


def test_token_reuse(ray_serve_app, sample_payload, verify_request_data):
    """Test that the same token can be verified multiple times"""
    base_url = ray_serve_app
    
    # Issue token once
    token_response = requests.post(f"{base_url}/token", json=sample_payload)
    token = token_response.json()["access_token"]
    
    # Verify multiple times with correct audience/issuer
    for _ in range(3):
        verify_response = requests.post(
            f"{base_url}/verify-token",
            json=verify_request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert verify_response.status_code == 200



# -------------------------
# Edge Case Tests (UNCHANGED)
# -------------------------
def test_very_large_payload(ray_serve_app):
    """Test token with very large payload"""
    base_url = ray_serve_app
    
    large_payload = {
        "user_name": "user_large",
        "role": "x" * 1000,
        "scope": [f"scope_{i}" for i in range(100)],
        "aud": AUDIENCE
    }
    
    response = requests.post(f"{base_url}/token", json=large_payload)
    
    assert response.status_code in [200, 413, 422]


def test_special_characters_in_payload(ray_serve_app, verify_request_data):
    """Test payload with special characters"""
    base_url = ray_serve_app
    
    payload = {
        "user_name": "user_special🎉🚀",
        "email": "test+special@example.com",
        "role": "Test User äöü 中文",
        "aud": AUDIENCE,
        "scope": ["read", "write"]
    }
    
    # Issue token
    token_response = requests.post(f"{base_url}/token", json=payload)
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    
    # Verify token
    verify_response = requests.post(
        f"{base_url}/verify-token",
        json=verify_request_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if verify_response.status_code == 200:
        verified = verify_response.json()
        assert verified["email"] == payload["email"]


# -------------------------
# Health Check Tests (UNCHANGED)
# -------------------------
def test_service_documentation_available(ray_serve_app):
    """Test that API documentation is available"""
    base_url = ray_serve_app
    
    response = requests.get(f"{base_url}/docs")
    assert response.status_code == 200


def test_openapi_schema_available(ray_serve_app):
    """Test that OpenAPI schema is available"""
    base_url = ray_serve_app
    
    response = requests.get(f"{base_url}/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/token" in schema["paths"]
    assert "/verify-token" in schema["paths"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])