import httpx
from pathlib import Path
import yaml

class ConfigurationClient:
    def __init__(self, base_url = "http://localhost:8001"):
        self.base_url = base_url    
        self.client = None

    async def startup(self):
        if self.client is None:
            # logger.info("Starting up ConfigurationClient httpx session")
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(None),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                ),
            )
    
    async def shutdown(self):
        if self.client:
            await self.client.aclose()
            # logger.info("Shutting down ConfigurationClient httpx session")
            self.client = None

    async def get_config_file(self,service_name:str):
        try:
            response = await self.client.get("/config/get_config_file", params={"service_name": service_name})
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