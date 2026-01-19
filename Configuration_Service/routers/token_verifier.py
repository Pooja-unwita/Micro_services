import jwt
import sys, os
from handlers.auth_handler import AuthenticationClient
from handlers.handler_config_loader import ConfigLoader
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


ISSUER = "Auth_Service"
AUDIENCE = "FE_Service"
security = HTTPBearer()
config_loder = ConfigLoader()
auth_config = config_loder.get_config(config_key="Authentication")
auth_client = AuthenticationClient(config=auth_config)

async def verify_token(token: HTTPAuthorizationCredentials = Depends(security))->dict: # need to remove some lines like unverified_header
    """
    Verifies the JWT token using the public keys from the JWKS endpoint.
    """
    token = token.credentials
    try:
       
        jwks_client = auth_client.jwt_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        
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























# import jwt
# from Handlers.auth_handler import jwks_client

# ISSUER = "http://localhost:8000"
# AUDIENCE = "Auth_Service"

# async def verify_token(token: str)->dict: # need to remove some lines like unverified_header
#     """
#     Verifies the JWT token using the public keys from the JWKS endpoint.
#     """
#     try:
#         import json
#         unverified_header = jwt.get_unverified_header(token)
#         print("\n--- Token Header (Unverified) ---")
#         print(json.dumps(unverified_header, indent=2))
#         if 'kid' in unverified_header:
#             print(f"Extracted KID from token header: {unverified_header['kid']}")
#         else:
#             print("KID not found in token header.")

#         signing_key = jwks_client.get_signing_key_from_jwt(token)

#         key_data = signing_key.key
#         print("\n--- Signing Key Found ---")
#         print(f"Key details: {key_data}")

#         payload = jwt.decode(
#             token,
#             signing_key.key,
#             algorithms=["RS256"],
#             audience=AUDIENCE,
#             issuer=ISSUER,
#         )
#         return payload
#     except Exception as e:
#         print(f"Token verification failed: {e}")
#         return None
