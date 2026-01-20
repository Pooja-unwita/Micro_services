import uvicorn
from fastapi import FastAPI
from urllib.parse import urlparse
from handlers.handler_config_loader import HandlerConfigLoader
from routers import auth

handler_config_loader= HandlerConfigLoader(service_name="Authentication_service",fetch_from_remote=True)
handler_config = handler_config_loader.get_config(config_key="Authentication")


base_url= handler_config["base_url"]
parsed = urlparse(base_url)
host = parsed.hostname
port = parsed.port
worker = handler_config["workers"]
app = FastAPI(
    title="Authentication Service",
    version="1.0.0"
)
app.include_router(auth.router)

if __name__ == "__main__":
    uvicorn.run(app, host=host, port=int(port), workers=worker)