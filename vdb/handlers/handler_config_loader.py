import yaml
from pathlib import Path
from typing import Dict, Any ,List, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)

CONFIG_ENCODING = "utf-8"
HANDLER_CONFIG_PATH = Path(__file__).parent / "handler_config.yaml"

class HandlerConfigLoader:
    config_encoding = CONFIG_ENCODING
    CONFIG_KEYS: List[str] = [
        "Embedding",
        "Authentication",
        "Configuration",
        "Milvus_Vector_Database",
        
    ]
    def __init__(self, 
                 
                 default_config_path: Path = HANDLER_CONFIG_PATH):
        """
        
        
        Args:
            service_name: Name of the current service
            default_config_path: Path to local handler_config.yaml
            fetch_from_remote: If True and local file missing, fetch from Config Service
            force_update: If True, always fetch from remote (ignores local cache)
            check_updates: If True, check if remote version is newer than local
        """
      
        self.default_config_path = default_config_path
      
        
        try:
            # Local file exists
            if self.default_config_path.exists():
                logger.info(f"Loading handler config from local file: {self.default_config_path}")
                self.default_config = self.load_yaml(self.default_config_path)
                   
            else:
                logger.error(f"Handler config not found at {self.default_config_path} and remote fetch is disabled or service_name not provided.")
                raise FileNotFoundError(
                    f"Handler config not found at {self.default_config_path} "
                    f"and remote fetch is disabled or service_name not provided."
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize ConfigLoader: {e}")
            raise RuntimeError(f"Failed to initialize ConfigLoader: {e}")    
            
    def load_yaml(self, yaml_path: str) -> Dict[str, Any]:
        logger.info(f"Loading YAML file: {yaml_path}")
        with open(yaml_path, "r", encoding=self.config_encoding) as file:
            return yaml.safe_load(file)
        
    def get_config(self, config_key: str) -> Dict[str, Any]:
        """Generic method to retrieve merged config for a given key."""
        logger.info(f"Retrieving config for key: {config_key}")
        return self.default_config.get(config_key, {})
           

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all known config sections in one dictionary."""
        logger.info("Retrieving all config sections.")
        return {key: self.get_config(key) for key in self.CONFIG_KEYS}