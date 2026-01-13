
from Embedding_Service.models.embed_input import Token
from fastapi import FastAPI, Depends, HTTPException, status ,APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from Configuration_Service.routers.services import SERVICES

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
ISSUER = "Authentication-service"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = APIRouter()


def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        unverified_payload = jwt.decode(
        token,
        "",  
        algorithms=[ALGORITHM],
        options={"verify_signature": False, "verify_exp": False, "verify_aud": False})
        
        service_name = unverified_payload.get("sub")
        caller=unverified_payload.get("aud")
        #ISSUER=unverified_payload.get("iss")
        if service_name is None:
            raise credentials_exception
        
        service_info = SERVICES.get(service_name)

        if not service_info:
            raise credentials_exception

        SECRET_KEY = service_info["secret"]
        payload = jwt.decode(
            token,SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=caller,
            issuer=ISSUER,
        )
        print(caller)
        return payload
    except JWTError:
        raise credentials_exception
