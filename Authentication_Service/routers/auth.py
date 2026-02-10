import jwt
from fastapi import FastAPI, APIRouter,HTTPException
from Authentication_Service.services.jwt_manager import JWTKeyManager
from Authentication_Service.models.models import Token, JWKS , VerifyRequest,TokenPayload
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ray import serve
import logging

logger = logging.getLogger('ray.serve')


ALGORITHM = "RS256"
app = FastAPI()
security = HTTPBearer()  

@serve.deployment
@serve.ingress(app)

class AuthService:

    def __init__(self, args: dict):
        
        self.key_manager = JWTKeyManager(keys_dict=args["KEYS"])
        
    @app.post("/token", response_model=Token)
    async def issue_access_token(self, payload: TokenPayload)-> Token: # use Form() if frontend comes
        """Issue a access token based on form inputs."""
        try:   
            payload_dict = payload.model_dump()
            token = await self.key_manager.create_access_token(payload_dict)
            logger.info("Access token issued successfully")
            return {"access_token": token, "token_type": "bearer"}
        except Exception as e:
            raise 


    @app.post("/verify-token", response_model=dict) # response model
    async def verify_token_endpoint(self, request: VerifyRequest, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        """
        Verifies the JWT token using the public keys from the JWKS endpoint.````
        """
        try:
            token = credentials.credentials
            public_key = await self.key_manager.get_key_from_jwks(token)
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[ALGORITHM],
                audience=request.AUDIENCE,
                issuer=request.ISSUER,
            )
            logger.info("Token verified successfully")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Token verification failed")