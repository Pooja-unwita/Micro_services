import jwt
import sys, os
from fastapi import HTTPException
from handlers.auth_handler import AuthenticationClient
from handlers.handler_config_loader import HandlerConfigLoader
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

ISSUER = "Auth_Service"
AUDIENCE = "FE_Service"
security = HTTPBearer()
config_loder = HandlerConfigLoader()
auth_config = config_loder.get_config(config_key="Authentication")
auth_client = AuthenticationClient(config=auth_config)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verifies the JWT token with the auth service.
    """
    token = credentials.credentials
    try:
        await auth_client.startup()
        payload = await auth_client.verify_token(
            token=token,
            issuer=ISSUER,
            audience=AUDIENCE
        )
        return payload
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")
 