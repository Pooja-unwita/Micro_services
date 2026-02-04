import os
import yaml
from pathlib import Path
from decouple import config
from fastapi import APIRouter, Query, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from models.config_input import ConfigInput
from services.config_service import ConfigurationService
from routers.token_verifier import verify_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
config_service = ConfigurationService()

@router.get("/get_config_file")
async def get_config_file(
    service_name: str = Query(...),
    token: dict = Depends(verify_token),
):
    logger.info(f"Received request for config file: {service_name}")
    return await config_service.get_config_file(service_name)








