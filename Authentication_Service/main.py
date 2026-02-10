from fastapi import logger
from Authentication_Service.routers.auth import AuthService
import logging
from pathlib import Path

def auth_app_builder(args: dict[str, str]):
        # Setup logging ONCE
    logger = logging.getLogger('ray.serve')
    logger.info("Building Authentication Service app with provided arguments")
    app = AuthService.bind(args=args)
    return app

