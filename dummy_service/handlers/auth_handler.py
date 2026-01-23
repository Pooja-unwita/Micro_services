import asyncio
import threading
from contextvars import ContextVar
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import httpx
import jwt
import requests
from utils.set_attribute import AttributeSetter

_token_context: ContextVar[Optional[str]] = ContextVar('auth_token', default=None)
_token_expiry_context: ContextVar[Optional[datetime]] = ContextVar('token_expiry', default=None)

# Locks for preventing duplicate token requests within same context
_token_lock = asyncio.Lock()

AUDIENCE = "FE_Service"

from contextvars import ContextVar
current_token = ContextVar('jwt_token')

class AuthenticationClient:

    def __init__(self, config:dict):
        AttributeSetter.set_attributes(self, config)
        self.client: Optional[httpx.AsyncClient] = None

    async def startup(self):
        try:
            if self.client is None:

                self.client = httpx.AsyncClient(
                                base_url=self.base_url,
                                timeout=self.timeout,
                                limits=httpx.Limits(
                                    max_connections=self.http_limits["max_connections"],
                                    max_keepalive_connections=self.http_limits["max_keepalive_connections"],
                                ),
                                headers=self.headers,
                            )            
        except Exception as e:
            raise e


    async def shutdown(self):
        """Close the connection pool gracefully."""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
        except Exception as e:
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
            print(f"Using cached token: {cached_token[:25]}...")
            return cached_token

        # Acquire lock to prevent multiple token requests in same context
        async with _token_lock:
            # Double-check after acquiring lock
            cached_token = _token_context.get()
            
            if cached_token:
                print(f"Using cached token (after lock): {cached_token[:25]}...")
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

                print(f"Obtained token: {token[:25]}...")
                return token
            except requests.exceptions.RequestException as e:
                print(f"Failed to get token: {e}")
                raise e

    
    async def verify_token(self, token: str, audience: str, issuer: str) -> Dict[str, Any]:
        """
        Verify a JWT token against the remote endpoint.
        """
        url = f"{self.base_url}/verify-token"
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        payload = {"AUDIENCE": audience, "ISSUER": issuer}
        
        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            print("Token verified successfully")
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Token verification failed: {e.response.text}")
            raise ValueError(f"Token verification failed: {e.response.text}")
        except httpx.RequestError as e:
            print(f"Request failed: {e}")
            raise
        
    def clear_token(self):
        """Clear cached token (useful for logout/refresh scenarios)."""
        try:
            _token_context.set(None)
            _token_expiry_context.set(None)
            print("Token cleared from context")
        except Exception as e:
            raise e