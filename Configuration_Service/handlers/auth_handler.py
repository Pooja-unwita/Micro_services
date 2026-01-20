import asyncio
import threading
from contextvars import ContextVar
from datetime import datetime, timedelta
from typing import Optional
import jwt
import requests
from utils.set_attribute import AttributeSetter
import logging

logger = logging.getLogger(__name__)

_token_context: ContextVar[Optional[str]] = ContextVar('auth_token', default=None)
_token_expiry_context: ContextVar[Optional[datetime]] = ContextVar('token_expiry', default=None)

# Locks for preventing duplicate token requests within same context
_token_lock = asyncio.Lock()

# AUDIENCE = "my-service"
AUDIENCE = "FE_Service"
# jwks_client = jwt.PyJWKClient(JWKS_URL)

from contextvars import ContextVar
current_token = ContextVar('jwt_token')

class AuthenticationClient:

    def __init__(self, config:dict):
        AttributeSetter.set_attributes(self, config)
        logger.info("AuthenticationClient initialized with config.")

    def jwt_client(self)-> jwt.PyJWKClient:
        """
        Returns a PyJWKClient instance for the JWKS endpoint.
        """
        try:
            JWKS_URL = f"{self.base_url}/.well-known/jwks.json"
            jwks_client = jwt.PyJWKClient(JWKS_URL)
            return jwks_client
        except Exception as e:
            logger.error(f"Failed to create JWKS client: {e}")
            raise e
        
    async def get_token(self) -> str:
        """
        Get token from context cache or request a new one.
        CONTEXT ISOLATION: Each async task gets its own token storage automatically.
        Task A's token is completely separate from Task B's token.
        """
        # Check if valid token exists in THIS task's context
        cached_token = _token_context.get()
        
        if cached_token:
            logger.info(f"Using cached token: {cached_token[:25]}...")
            return cached_token

        # Acquire lock to prevent multiple token requests in same context
        async with _token_lock:
            # Double-check after acquiring lock
            cached_token = _token_context.get()
            
            if cached_token:
                logger.info(f"Using cached token (after lock): {cached_token[:25]}...")
                return cached_token

            # Request new token
            try:
                token_request_payload = {
                    "user_name": "test-user",
                    "scope": ["read:data", "write:data"],
                    "aud": AUDIENCE
                }
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.post(
                        f"{self.base_url}/token",
                        json=token_request_payload,
                        timeout=self.timeout, 
                        headers=self.headers
                    )
                )
                response.raise_for_status()
                token = response.json()["access_token"]

                # Store token and expiry in THIS task's context
                _token_context.set(token)

                logger.info(f"Obtained new token: {token[:25]}...")
                return token
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to get token: {e}")
                raise


        
    def clear_token(self):
        """Clear cached token (useful for logout/refresh scenarios)."""
        try:
            _token_context.set(None)
            _token_expiry_context.set(None)
            logger.info("Token cleared from context")
        except Exception as e:
            raise e
