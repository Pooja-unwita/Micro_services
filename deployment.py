import subprocess
import sys
import time
import shutil
from pathlib import Path
import os

# ----------------------------
# Paths
# ----------------------------

ROOT_DIR = Path(__file__).resolve().parent

CONFIG_SERVICE_DIR = ROOT_DIR / "Configuration_Service"
CONFIG_MAIN = CONFIG_SERVICE_DIR / "main.py"
GENERATED_CONFIG = CONFIG_SERVICE_DIR / "config_files" / "handler_config.yaml"

SERVICES = [
    ROOT_DIR / "Authentication_Service",
    ROOT_DIR / "Embedding_Service",
    ROOT_DIR / "vdb",
]

WAIT_TIMEOUT = 30  # seconds
POLL_INTERVAL = 1  # seconds


# ----------------------------
# Helpers
# ----------------------------

def run_configuration_service():
    print("Starting Configuration Service...")

    return subprocess.Popen(
        [sys.executable, str(CONFIG_MAIN)],
        cwd=str(ROOT_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def wait_for_handler_config():
    print("Waiting for handler_config.yaml to be generated...")

    waited = 0
    while waited < WAIT_TIMEOUT:
        if GENERATED_CONFIG.exists():
            print("handler_config.yaml detected")
            return
        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL

    raise TimeoutError("handler_config.yaml was not generated within timeout")


def distribute_config():
    print("Distributing handler_config.yaml to services...")

    for service in SERVICES:
        handlers_dir = service / "handlers"

        if not handlers_dir.exists():
            os.makedirs(handlers_dir)

        destination = handlers_dir / "handler_config.yaml"
        shutil.copy2(GENERATED_CONFIG, destination)

        print(f"Copied to {destination}")


# ----------------------------
# Main Deployment Flow
# ----------------------------

def main():
    config_process = None

    try:
        config_process = run_configuration_service()
        wait_for_handler_config()
        distribute_config()

        print("\nDeployment completed successfully")

    except Exception as e:
        print(f"\n Deployment failed: {e}")
        if config_process:
            config_process.terminate()
        sys.exit(1)


if __name__ == "__main__":
    main()
