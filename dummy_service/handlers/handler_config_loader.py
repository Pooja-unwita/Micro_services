import yaml
from pathlib import Path
from typing import Dict, Any ,List
import asyncio
from handlers.bootstrap_client import BootstrapClient

CONFIG_ENCODING = "utf-8"
HANDLER_CONFIG_PATH = Path(__file__).parent / "handler_config.yaml"

class HandlerConfigLoader:
    config_encoding = CONFIG_ENCODING
    CONFIG_KEYS: List[str] = [
        "Embedding",
        "Authentication",
        "Configuration"
        
    ]
    def __init__(self, 
                 service_name: str = None,
                 default_config_path: Path = HANDLER_CONFIG_PATH,
                 fetch_from_remote: bool = False):
        """
        Initialize ConfigLoader with bootstrap capability
        
        Args:
            service_name: Name of the current service (e.g., "Authentication_Service")
            default_config_path: Path to local handler_config.yaml
            fetch_from_remote: If True and local file missing, fetch from Config Service
        """
        self.service_name = service_name
        self.default_config_path = default_config_path
        self.fetch_from_remote = fetch_from_remote
        
        try:
            # Try loading local config first
            if self.default_config_path.exists():
                print(f"Loading handler config from local file: {self.default_config_path}")
                self.default_config = self.load_yaml(self.default_config_path)
            
            elif self.fetch_from_remote and self.service_name:
                # Fetch from Configuration Service
                print(f"Local handler config not found. Fetching from Configuration Service...")
                self.default_config = asyncio.run(self._fetch_remote_config())
                
                # Optionally save it locally for future use
                self._save_config_locally(self.default_config)
            
            else:
                raise FileNotFoundError(
                    f"Handler config not found at {self.default_config_path} "
                    f"and remote fetch is disabled or service_name not provided."
                )
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ConfigLoader: {e}")

    async def _fetch_remote_config(self) -> Dict[str, Any]:
        """Fetch handler config from Configuration Service using bootstrap client"""
        bootstrap_client = BootstrapClient()
        # fetch_handler_config now returns bytes (response.content)
        yaml_bytes = await bootstrap_client.fetch_handler_config(self.service_name)
        # Parse YAML bytes to dictionary
        config_dict = yaml.safe_load(yaml_bytes)
        return config_dict
    
    def _save_config_locally(self, config: Dict[str, Any]):
        """Save fetched config locally for caching"""
        try:
            self.default_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.default_config_path, "w", encoding=self.config_encoding) as file:
                yaml.safe_dump(config, file, sort_keys=False)
            print(f"Cached handler config locally at {self.default_config_path}")
        except Exception as e:
            print(f"Warning: Could not cache config locally: {e}")
        
            
    def load_yaml(self, yaml_path: str) -> Dict[str, Any]:
        with open(yaml_path, "r", encoding=self.config_encoding) as file:
            return yaml.safe_load(file)
        
    def get_config(self, config_key: str) -> Dict[str, Any]:
        """Generic method to retrieve merged config for a given key."""
        return self.default_config.get(config_key, {})
           

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all known config sections in one dictionary."""
        return {key: self.get_config(key) for key in self.CONFIG_KEYS}