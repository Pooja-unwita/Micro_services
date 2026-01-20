# from typing import tuple
import httpx
from pathlib import Path
import yaml
import asyncio
from utils.set_attribute import AttributeSetter
import logging

logger = logging.getLogger(__name__)


class ConfigurationClient:
    def __init__(self, config:dict):
        AttributeSetter.set_attributes(self, config)  
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.client = None
        logger.info("ConfigurationClient initialized.")
        

    async def startup(self):
        try:
            if self.client is None:
                logger.info("Starting up httpx.AsyncClient for ConfigurationClient.")
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
            logger.error(f"Failed to startup ConfigurationClient: {e}")
            raise e
          

    async def shutdown(self):
        """Close the connection pool gracefully."""
        try:
            if self.client:
                logger.info("Shutting down httpx.AsyncClient for ConfigurationClient.")
                await self.client.aclose()
                self.client = None
        except Exception as e:
            logger.error(f"Failed to shutdown ConfigurationClient: {e}")
            raise e


    async def fetch_config(self,service_name:str, token: str) -> tuple[dict,Path]:
        
        try:
            if not self.client:
                await self.startup()
        except Exception as e:
            logger.error(f"Failed to startup client in fetch_config: {e}")
            raise e
        async with self.semaphore:
            try:
                _headers = {
                        **self.headers,
                        "Authorization": f"Bearer {token}",
                        }
                logger.info(f"Fetching config for service: {service_name}")
                response = await self.client.get("/get_config_file", params={"service_name": service_name}, headers=_headers)

                
                content_disposition=response.headers.get("Content-Disposition")
                filename=content_disposition.split("filename=")[-1].strip('"')
                response.raise_for_status()
                yaml_data = yaml.safe_load(response.content)
            
                return yaml_data, filename
            

                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching config: {e}")
                raise RuntimeError(
                    f"HTTP {e.response.status_code} from /config: {e.response.text}"
                )
            except httpx.RequestError as e:
                logger.error(f"Request error fetching config: {e}")
                raise RuntimeError(f"Error contacting {self.base_url}/config: {e}")
            

    async def save_yaml(self,data: dict,output_dir: Path,filename: str,) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / filename

        with file_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
        logger.info(f"YAML config saved to {file_path}")
        return file_path
        
        
