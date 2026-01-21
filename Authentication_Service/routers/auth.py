import jwt
import sys, os
from fastapi import APIRouter
from services.jwt_manager import JWTKeyManager
from models.models import Token, JWKS ,VeifyRequest
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="", tags=["Authentication"])
key_manager = JWTKeyManager()
security = HTTPBearer()


@router.post("/token", response_model=Token)
async def issue_access_token(payload:dict)-> Token: # use Form() if frontend comes
    """Issue a access token based on form inputs."""
    try:   
        token = await key_manager.create_access_token(payload)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise e


@router.post("/verify-token")
async def verify_token(request: VeifyRequest, token: HTTPAuthorizationCredentials = Depends(security),)->dict: # need to remove some lines like unverified_header
    """
    Verifies the JWT token using the public keys from the JWKS endpoint.
    """
    try:
        token = token.credentials
        public_key = await key_manager.get_key_from_jwks(token)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=request.AUDIENCE,
            issuer=request.ISSUER,
        )
        return payload
    except Exception as e:
        raise Exception (f"Token verification failed: {e}")