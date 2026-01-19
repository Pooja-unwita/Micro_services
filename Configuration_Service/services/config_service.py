from ray import serve
from pathlib import Path
from fastapi import APIRouter, Query, Depends
from fastapi.responses import FileResponse


from routers.token_verifier import verify_token

import uvicorn

router = APIRouter()


from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse


class ConfigurationService:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config_files"
        self.service_file_map = {
            "Embedding_Service": "embed.yaml",
            "VectorDB_Service": "vectordb.yaml",
            "Ingestion_Service": "ingestion.yaml",
            "Handler" : "handler_config.yaml",
            "Ray_Cluster": "ray_cluster.yaml",
            "Service" : "service_runtime.yaml"
        }

    async def get_config_file(self, service_name: str) -> FileResponse:
        if service_name not in self.service_file_map:
            raise HTTPException(400, "Unknown service name")

        config_path = self.config_dir / self.service_file_map[service_name]
        if not config_path.is_file():
            raise HTTPException(404, "Config file not found")

        return FileResponse(
            config_path,
            media_type="application/x-yaml",
            filename=config_path.name,
        )

            
