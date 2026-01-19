import sys
import os
from fastapi import APIRouter
from services.jwt_manager import JWTKeyManager,KEYS
from models.models import Token, JWKS

router = APIRouter(prefix="", tags=["Authentication"])
key_manager = JWTKeyManager()

@router.get("/.well-known/jwks.json", response_model=JWKS)
async def jwks()-> JWKS:
    """Expose the JSON Web Key Set (JWKS) endpoint."""
    try:
        jwks_keys = []
        for kid, key in KEYS.items():
            public_key = await key_manager.load_public_key(key["public"])
            jwks_keys.append(await key_manager.public_key_to_jwk(public_key, kid))
        return {"keys": jwks_keys}
    except Exception as e:
        raise e

@router.post("/token", response_model=Token)
async def issue_access_token(payload:dict)-> Token: # use Form() if frontend comes
    """Issue a access token based on form inputs."""

    try:   
       
        token = await key_manager.create_access_token(payload)
        
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise e




        


        