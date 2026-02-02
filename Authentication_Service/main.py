import uvicorn
from fastapi import FastAPI
from urllib.parse import urlparse
from Authentication_Service.routers.auth import AuthService


def auth_app_builder(args: dict[str, str]):
    app = AuthService.bind()
    return app

