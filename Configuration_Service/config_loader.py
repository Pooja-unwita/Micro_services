from ray import serve
from pathlib import Path
from fastapi import FastAPI, HTTPException,Query,Depends
from fastapi.responses import FileResponse
from Configuration_Service.models.config_input import ConfigInput

    
app = FastAPI()

@serve.deployment
@serve.ingress(app)
class ConfigurationService:
    """
    A Ray Serve deployment that provides configuration files for various services.
    
    This service acts as a centralized configuration provider, mapping service names
    to their corresponding configuration files and serving them via HTTP endpoints.
    
    Attributes:
        service_file_map (dict): A mapping of service names to their config file names.
    """
    
    def __init__(self):
        """
        Initialize the Configuration Service.
        
        Sets up the mapping between service names and their corresponding
        configuration file names.
        """
        try:
            self.base_dir = Path(__file__).parent
            self.config_dir =self.base_dir / "config_files"
            self.service_file_map = {
                    "Embedding_Service": "embed.yaml",
                    "VectorDB_Service" : "vectordb.yaml",
                    "Ingestion_Service": "ingestion.yaml"
                }
        except Exception as e:
            raise 
 
            

    @app.get("/get_config_file")
    async def get_config(self, service_name: str = Query()): 
        """
        Retrieve and serve a configuration file for the specified service.
        
        This endpoint accepts a service name and returns the corresponding
        configuration file as a YAML file download.
        
        Args:
            service_name (str): The name of the service requesting configuration.
                               Must be one of the keys in service_file_map.
        
        Returns:
            FileResponse: The configuration file as a downloadable YAML file.
        
        Raises:
            HTTPException: 
                - 400 if the service name is not recognized
                - 500 if the config file is not found or other unexpected errors occur
        
        Example:
            POST /config
            Body: {"service_name": "Embedding_Service"}
            
            Returns: embed.yaml file as download
        """
        try:
            if service_name not in self.service_file_map:
                raise HTTPException(
                    status_code=400,
                    detail="Unknown service name"
                )

            config_filename = self.service_file_map[service_name]
            config_path = self.config_dir / config_filename
            if not config_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail="Config file not found"
                )

            return FileResponse(
                path=config_path,
                media_type="application/x-yaml",
                filename=config_path.name
            )
        
        except HTTPException:
            raise 

        except Exception as e:
            raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while serving config: {str(e)}"
        )
            
config_app = ConfigurationService.bind()