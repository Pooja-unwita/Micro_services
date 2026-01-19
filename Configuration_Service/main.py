import logging
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
CONFIG_FILE= BASE_DIR / "config_files" / "service_runtime.yaml"


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

if __name__ == "__main__":
    try:
        config = load_config(CONFIG_FILE)
        host = config["configuration"]["host"]
        port = config["configuration"]["port"]
        workers =config ["configuration"]["workers"]
        logger.info(f"Starting Configuration Service on {host}:{port}")
        uvicorn.run(app, host=host, port=port, workers=workers)

    except KeyboardInterrupt:
        logger.info("Configuration Service stopped by user")

    except Exception as e:
        logger.exception("Failed to start Configuration Service")
        raise SystemExit(1)

