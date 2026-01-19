import yaml
from pathlib import Path
from typing import Dict, Any ,List
import unittest

CONFIG_ENCODING = "utf-8"
HANDLER_CONFIG_PATH = Path(__file__).parent / "handler_config.yaml"

class ConfigLoader:
    config_encoding = CONFIG_ENCODING
    CONFIG_KEYS: List[str] = [
        "Embedding",
        "Authentication",
        "Configuration"
        
    ]
    def __init__(self, default_config_path: str = HANDLER_CONFIG_PATH):
        self.default_config_path = default_config_path
        
        self.default_config = self.load_yaml(self.default_config_path)
       

    def load_yaml(self, yaml_path: str) -> Dict[str, Any]:
        with open(yaml_path, "r", encoding=self.config_encoding) as file:
            return yaml.safe_load(file)
        
    def get_config(self, config_key: str) -> Dict[str, Any]:
        """Generic method to retrieve merged config for a given key."""
        return self.default_config.get(config_key, {})
           

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all known config sections in one dictionary."""
        return {key: self.get_config(key) for key in self.CONFIG_KEYS}