
import jwt
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from Handlers.auth_handler import AuthenticationClient

ISSUER = "http://localhost:8000"
AUDIENCE = "Auth_Service"

auth_client = AuthenticationClient()

async def verify_token(token: str)->dict: # need to remove some lines like unverified_header
    """
    Verifies the JWT token using the public keys from the JWKS endpoint.
    """
    try:
        import json
        unverified_header = jwt.get_unverified_header(token)
        # print("\n--- Token Header (Unverified) ---")
        # print(json.dumps(unverified_header, indent=2))
        # if 'kid' in unverified_header:
        #     print(f"Extracted KID from token header: {unverified_header['kid']}")
        # else:
        #     print("KID not found in token header.")
        jwks_client = auth_client.jwt_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        key_data = signing_key.key
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
