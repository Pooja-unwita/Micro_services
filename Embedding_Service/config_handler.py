import logging
import httpx
from auth_handler import AuthenticationClient 
from pathlib import Path
import yaml

class ConfigurationClient:
    def __init__(self, caller:str , base_url = "http://localhost:8001/config",):
        self.base_url = base_url  
        self.caller  = caller
        self.client = None
        self.auth_client=AuthenticationClient(service_name="configuration_service")
        #self.service_name = "Embedding_Service"
        self._headers = {"Content-Type": "application/json"}

    async def startup(self):
        if self.client is None:
            token=await self.auth_client.get_token(self.caller)
            
            self._headers["Authorization"] = f"Bearer {token['access_token']}"

           
            # logger.info("Starting up ConfigurationClient httpx session")
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(None),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                ),
            )
            print(self._headers)
            self.client.headers.update(self._headers)
            print(self.client.headers)

    async def shutdown(self):
        if self.client:
            await self.client.aclose()
            # logger.info("Shutting down ConfigurationClient httpx session")
            self.client = None

    async def get_config_file(self,service_name:str):
        try:
            response = await self.client.get("/get_config_file", params={"service_name": service_name})
            print(f"Response headers: {response.headers}")
            content_disposition=response.headers.get("Content-Disposition")
            filename=content_disposition.split("filename=")[-1].strip('"')
            response.raise_for_status()
            yaml_data = yaml.safe_load(response.content)
            output_path = Path.cwd() / "embed.yaml"
            with output_path.open("w") as f:
                yaml.safe_dump(yaml_data, f)
            print(f"YAML file saved at: {output_path}")
            return output_path

        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"HTTP {e.response.status_code} from /config: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise RuntimeError(f"Error contacting {self.base_url}/config: {e}")