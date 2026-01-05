
from Embedding_Service.models.embed_input import Token
from fastapi import FastAPI, Depends, HTTPException, status ,APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from Embedding_Service.routers.services import SERVICES

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
ISSUER = "embedding-service"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = APIRouter()

def create_access_token(data: dict, secret_key: str):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return token

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    service_name = form_data.username
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
        "aud": service_info.get("audience"),
        "scope": service_info.get("scope"),
    }

    access_token = create_access_token(
        data=access_token_payload, secret_key=service_info["secret"]
    )
    return {"access_token": access_token, "token_type": "bearer"}

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

        if service_name is None:
            raise credentials_exception
        
        service_info = SERVICES.get(service_name)

        if not service_info:
            raise credentials_exception

        SECRET_KEY = service_info["secret"]
        payload = jwt.decode(
            token,SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=service_info.get("audience"),
            issuer=ISSUER,
        )
        return payload
    except JWTError:
        raise credentials_exception
