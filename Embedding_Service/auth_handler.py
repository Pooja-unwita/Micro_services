import logging
import httpx
from pathlib import Path
import yaml

class AuthenticationClient:
    def __init__(self, service_name: str, base_url = "http://localhost:8001/auth"):
        self.base_url = base_url    
        self.client = None
        self.service_name = service_name
        self._headers = {"Content-Type": "application/json"}

    async def get_token(self,caller):
        """
        Fetch a JWT token from the embedding service's /token endpoint.
        This method does NOT retry itself; retry is handled in _post().
        """
        async with httpx.AsyncClient() as client:
            token_url = f"{self.base_url}/token"
            response = await client.post(
                token_url,
                data={
                    "username": self.service_name,
                    "password": " ",
                    "client_id": caller,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token = response.json()
            # self._headers["Authorization"] = f"Bearer {token['access_token']}"
            return token
            #logging.info("Successfully obtained new auth token.")

