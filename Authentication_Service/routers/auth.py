import jwt
import sys, os
from fastapi import APIRouter,HTTPException
from services.jwt_manager import JWTKeyManager
from models.models import Token, JWKS , VerifyRequest
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ray import serve
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
async def verify_token_endpoint(request: VerifyRequest, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verifies the JWT token using the public keys from the JWKS endpoint.
    """
    try:
        token = credentials.credentials
        public_key = await key_manager.get_key_from_jwks(token)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=request.AUDIENCE,
            issuer=request.ISSUER,
        )
        print("Token verified successfully")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")
    

 