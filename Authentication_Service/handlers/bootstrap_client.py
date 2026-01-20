# handlers/bootstrap_client.py
import httpx
import os
from typing import Dict
import yaml
from decouple import config
class BootstrapClient:
    """
    Minimal client for fetching handler configs from Configuration Service
    Does NOT require handler.yaml to initialize
    """
    
    def __init__(self):
        # Get these from environment variables
        self.config_service_url = config(
            "CONFIG_SERVICE_URL"
        )
        self.service_api_key = config("SERVICE_API_KEY")
        
        if not self.service_api_key:
            raise ValueError(
                "SERVICE_API_KEY environment variable must be set. "
                "This is used for service-to-service authentication."
            )
    
    async def fetch_handler_config(self, service_name: str) -> Dict:
        """
        Fetch handler.yaml from Configuration Service
        Uses service API key (not user token) for authentication
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.config_service_url}/bootstrap/handler",
                    params={"service_name": service_name},
                    headers={"X-Service-Key": self.service_api_key}
                )
                response.raise_for_status()
             
                # return response.json()
                return response.content
                
            except httpx.HTTPStatusError as e:
                raise RuntimeError(
                    f"Failed to fetch handler config: HTTP {e.response.status_code} - {e.response.text}"
                )
            except httpx.RequestError as e:
                raise RuntimeError(
                    f"Error contacting Configuration Service at {self.config_service_url}: {e}"
                )