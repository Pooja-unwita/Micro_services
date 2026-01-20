import logging
from urllib.parse import urlparse
from routers import config_loader
from fastapi import FastAPI
import uvicorn
import yaml
from pathlib import Path



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
    level= logging.INFO)
logger = logging.getLogger(__name__)



app = FastAPI()
app.include_router(config_loader.router)


BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE= BASE_DIR / "config_files" / "handler_config.yaml"
CLUSTER_CONFIG_FILE= BASE_DIR / "config_files" / "ray_cluster.yaml"


def load_config(path: Path) -> dict:
    if not path.exists():
        logger.error(f"Config file not found: {path}")
        raise FileNotFoundError(path)

    try:
        with path.open("r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {path}")
        raise e

def check_configs():
    logger.info("Checking and updating handler and cluster configs")
    handler_config=load_config(CONFIG_FILE)
    cluster_config=load_config(CLUSTER_CONFIG_FILE)
    applications = cluster_config.get("applications", [])

    if not isinstance(applications, list):
        logger.error(f"'applications'in {CLUSTER_CONFIG_FILE.name} must be a list")
        raise ValueError(f"'applications' in {CLUSTER_CONFIG_FILE.name}  must be a list")

    # Build lookup table from embed.yaml
    app_index = {
        app["name"].split("_")[0]: app
        for app in applications
        if isinstance(app, dict) and "name" in app
    }
    if not app_index:
        logger.error(f"No valid applications found in {CLUSTER_CONFIG_FILE.name}")
        raise ValueError(f"No valid applications found in {CLUSTER_CONFIG_FILE.name}")

    auth_name = list(handler_config.keys())

    for i in auth_name:
        if i in app_index.keys():
            app = app_index[i]
            route_prefix = app.get("route_prefix")
            http_options = cluster_config.get("http_options")
            host=http_options.get("host")
            port=http_options.get("port")
            base_url=f"http://{host}:{port}{route_prefix}"
            handler_config[i].update({
                "base_url": base_url
            })

    with CONFIG_FILE.open("w") as f:
        yaml.safe_dump(handler_config, f, sort_keys=False)

    logger.info(f"{CONFIG_FILE.name} successfully interpreted from {CLUSTER_CONFIG_FILE.name}")

if __name__ == "__main__":
    try:
        logger.info("Starting Configuration Service initialization")
        check_configs()
        config = load_config(CONFIG_FILE)
        base_url= config["Configuration"]["base_url"]
        parsed = urlparse(base_url)
        host = parsed.hostname
        port = parsed.port
        num =config ["Configuration"]["workers"]
      
        logger.info(f"Starting Configuration Service on {host}:{port}")
        uvicorn.run("main:app", host=host, port=port, workers=num)
        logger.info("Configuration Service started successfully")

    except KeyboardInterrupt:
        logger.info("Configuration Service stopped by user")

    except Exception as e:
        logger.exception("Failed to start Configuration Service")
        raise SystemExit(1)

 