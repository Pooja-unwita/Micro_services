
#from Embedding_Service.models.embed_input import Token
from fastapi import FastAPI, Depends, HTTPException, status ,APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from Authentication_Service.services import SERVICES
from pydantic import BaseModel
from ray import serve

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ISSUER = "Authentication-service"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

app = FastAPI()
@serve.deployment
@serve.ingress(app)
class AuthenticationService:
    def __init__(self):
        pass

    async def create_access_token(self,data: dict, secret_key: str):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
        return token

    @app.post("/token", response_model=Token)
    async def login_for_access_token(self,form_data: OAuth2PasswordRequestForm = Depends()):
        service_name = form_data.username
        caller= form_data.client_id
        service_info = SERVICES.get(service_name)
        if not service_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service name or secret key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_payload = {
            "sub": service_name,
            "iss": ISSUER,
            "aud": caller,
            "scope": service_info.get("scope"),
        }

        access_token = await self.create_access_token(
            data=access_token_payload, secret_key=service_info["secret"]
        )
        return {"access_token": access_token, "token_type": "bearer"}

auth_app=AuthenticationService.bind()