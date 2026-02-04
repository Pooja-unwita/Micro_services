import jwt
from fastapi import FastAPI, APIRouter,HTTPException
from Authentication_Service.services.jwt_manager import JWTKeyManager
from Authentication_Service.models.models import Token, JWKS , VerifyRequest
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ray import serve

app = FastAPI()
security = HTTPBearer()  

@serve.deployment
@serve.ingress(app)

class AuthService:

    def __init__(self):
        
        self.key_manager = JWTKeyManager()
        
    @app.post("/token", response_model=Token)
    async def issue_access_token(self, payload:dict)-> Token: # use Form() if frontend comes
        """Issue a access token based on form inputs."""
        try:   
            token = await self.key_manager.create_access_token(payload)
            return {"access_token": token, "token_type": "bearer"}
        except Exception as e:
            raise e


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