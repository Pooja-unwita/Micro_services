import os
import yaml
from pathlib import Path
from decouple import config
from fastapi import APIRouter, Query, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from models.config_input import ConfigInput
from services.config_service import ConfigurationService
from routers.token_verifier import verify_token

router = APIRouter()
config_service = ConfigurationService()

@router.get("/get_config_file")
async def get_config_file(
    service_name: str = Query(...),
    token: dict = Depends(verify_token),
):
  
    return await config_service.get_config_file(service_name)


# Service API Key - stored in environment variable
SERVICE_API_KEY = config("SERVICE_API_KEY", "change-me-in-production")

@router.get("/bootstrap/handler")
async def get_handler_config(
    service_name: str = Query(..., description="Name of the service requesting config"),
    x_service_key: str = Header(None, description="Service API key for authentication")
):
    """
    Bootstrap endpoint for services to fetch their handler.yaml
    Uses service-to-service API key (NOT user tokens)
    
    This endpoint is called during service startup before any user authentication
    """
    
    # Verify service API key
    if x_service_key != SERVICE_API_KEY:
        raise HTTPException(
            status_code=403, 
            detail="Invalid or missing service API key"
        )
    
    # Construct path to handler config
    config_path = Path(__file__).parent.parent / "config_files" / "handler_config.yaml"
    
    if not config_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Handler config not found for service: {service_name}"
        )
    
    try:
        return await config_service.get_config_file(service_name="Handler")
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return config_data
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading handler config: {str(e)}"
        )



