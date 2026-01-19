
import jwt
import sys, os
from fastapi import Depends
from Embedding_Service.handlers.auth_handler import AuthenticationClient
from Embedding_Service.handlers.handler_config_loader import ConfigLoader
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=True)
#"torch>=2.9.1"
ISSUER = "Auth_Service"
AUDIENCE = "FE_Service"

config_loader = ConfigLoader()
auth_config = config_loader.get_config("Authentication")
auth_client = AuthenticationClient(config=auth_config)



async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security),)->dict: # need to remove some lines like unverified_header
    """
    Verifies the JWT token using the public keys from the JWKS endpoint.
    """
    token = credentials.credentials
    try:
        import json
        unverified_header = jwt.get_unverified_header(token)
        jwks_client = auth_client.jwt_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # key_data = signing_key.key
        # print("\n--- Signing Key Found ---")
        # print(f"Key details: {key_data}")

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
        )
        return payload
    except Exception as e:
        raise Exception (f"Token verification failed: {e}")
        # print(f"Token verification failed: {e}")
        # return None
