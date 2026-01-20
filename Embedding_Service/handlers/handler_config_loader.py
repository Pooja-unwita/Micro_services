import yaml
from pathlib import Path
from typing import Dict, Any ,List, Tuple
import asyncio
from Embedding_Service.handlers.bootstrap_client import BootstrapClient

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
                 fetch_from_remote: bool = True,
                 force_update: bool = False,
                 check_updates: bool = True):
        """
        Initialize ConfigLoader with bootstrap capability
        
        Args:
            service_name: Name of the current service
            default_config_path: Path to local handler_config.yaml
            fetch_from_remote: If True and local file missing, fetch from Config Service
            force_update: If True, always fetch from remote (ignores local cache)
            check_updates: If True, check if remote version is newer than local
        """
        self.service_name = service_name
        self.default_config_path = default_config_path
        self.fetch_from_remote = fetch_from_remote
        
        try:
            # Force update - always fetch from remote
            if force_update and self.service_name:
                print("Force update enabled. Fetching from Configuration Service...")
                remote_bytes, self.default_config = asyncio.run(self._fetch_remote_config())
                self._save_config_locally_bytes(remote_bytes)
            
            # Local file exists
            elif self.default_config_path.exists():
                print(f"Loading handler config from local file: {self.default_config_path}")
                self.default_config = self.load_yaml(self.default_config_path)
                
                # Check if remote version is newer
                if check_updates and self.service_name:
                    needs_update , config_bytes, config_dict = asyncio.run(self._should_update())
                    if needs_update: 
                        self.default_config = config_dict                     
                        self._save_config_locally_bytes(config_bytes)
            
            # No local file - fetch from remote
            elif self.fetch_from_remote and self.service_name:
                print("Local handler config not found. Fetching from Configuration Service...")
                remote_bytes, self.default_config = asyncio.run(self._fetch_remote_config())
                self._save_config_locally_bytes(remote_bytes)
            
            else:
                raise FileNotFoundError(
                    f"Handler config not found at {self.default_config_path} "
                    f"and remote fetch is disabled or service_name not provided."
                )
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ConfigLoader: {e}")
        
    async def _should_update(self) -> Tuple[bool, bytes, Dict[str, Any]]:
        """
        Check if remote config is newer than local
        
        Returns:
            Tuple[bool, bytes, Dict]: (needs_update, config_bytes, config_dict)
                - needs_update: True if remote differs from local
                - config_bytes: Remote config bytes if update needed, else local bytes
                - config_dict: Remote config dict if update needed, else current dict
        """
        try:
            
            
            # Get remote version and bytes
            remote_bytes, remote_config = await self._fetch_remote_config()
            
            
            # Get local version's bytes
            local_bytes = self._get_local_bytes()
            
            if not local_bytes:
                # No local version info, assume update needed
                return True, remote_bytes, remote_config
            
            # Compare versions (simple string comparison, or use packaging.version for semver)
            if remote_bytes != local_bytes:
                
                return True, remote_bytes, remote_config
            
            return False, local_bytes, self.default_config
            
        except Exception as e:
            try:
                local_bytes = self._get_local_bytes()
            except Exception:
                local_bytes = b''
            print(f"Error checking for updates: {e}")
            return False, local_bytes, self.default_config
    
    def _get_local_bytes(self) -> bytes:
        """Read local config file as raw bytes"""
        with open(self.default_config_path, 'rb') as f:
            return f.read()

    async def _fetch_remote_config(self) -> tuple[bytes,Dict[str, Any]]:
        """Fetch handler config from Configuration Service using bootstrap client"""
        bootstrap_client = BootstrapClient()
        # fetch_handler_config now returns bytes (response.content)
        yaml_bytes = await bootstrap_client.fetch_handler_config(self.service_name)
        # Parse YAML bytes to dictionary
        config_dict = yaml.safe_load(yaml_bytes)
        return yaml_bytes, config_dict
    
    def _save_config_locally_bytes(self, content: bytes):
        """Save raw bytes to local config file (preserves exact format)"""
        try:
            self.default_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.default_config_path, "wb") as file:  # ✅ Write binary
                file.write(content)
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