from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse

import logging
logger = logging.getLogger(__name__)

class ConfigurationService:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config_files"
        self.service_file_map = {
            "Handler" : "handler_config.yaml",
            "Ray_Cluster": "ray_cluster.yaml",
            
        }
        logger.info("ConfigurationService initialized.")

    async def get_config_file(self, service_name: str) -> FileResponse:
        logger.info(f"Request to get config file for service: {service_name}")
        if service_name not in self.service_file_map:
            raise HTTPException(400, "Unknown service name")

        config_path = self.config_dir / self.service_file_map[service_name]
        if not config_path.is_file():
            logger.error(f"Config file not found: {config_path}")
            raise HTTPException(404, "Config file not found")

        return FileResponse(
            config_path,
            media_type="application/x-yaml",
            filename=config_path.name,
        )

            
