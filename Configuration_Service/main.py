import subprocess
import sys
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
    level= logging.INFO)
logger = logging.getLogger(__name__)

def run_serve_cli(config_path: str):
    """Run 'serve run' CLI command with the config file."""
    
    logger.info(f"\nStarting Ray Serve with: serve run {config_path}")
    logger.info("="*60)
    
    try:
        # Run the serve command - this will block until interrupted
        # Use --blocking flag to keep the process running
        process = subprocess.run(
            ["serve", "run", config_path],
            check=True,
            # Don't capture output - let it stream to console
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        
    except subprocess.CalledProcessError as e:
        logger.error(f"\nServe command failed with exit code {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.error("\n\nReceived interrupt signal, shutting down...")
        sys.exit(0)

def main():
    config_file = "Configuration_Service/config_files/config.yaml"
    run_serve_cli(config_file)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("\n\nReceived interrupt signal, shutting down...")


#################################################
# import subprocess
# import sys
# import logging
# import requests
# import yaml
# import os

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
#     level=logging.INFO)
# logger = logging.getLogger(__name__)

# CONFIG_URL = r"C:\Users\Abina\Documents\serve_ray\Configuration_Service\config_files\config.yaml"
# LOCAL_CONFIG_PATH = "embed_runtime.yaml"  # Temporary local copy


# def fetch_config() -> dict:
#     """Fetch configuration from config service (or local file)."""
#     try:
#         # Check if CONFIG_URL is a local file path
#         if os.path.exists(CONFIG_URL):
#             logger.info(f"Reading config from local file: {CONFIG_URL}")
#             with open(CONFIG_URL, 'r') as f:
#                 config = yaml.safe_load(f)
#         else:
#             # Fetch from remote URL
#             logger.info(f"Fetching config from URL: {CONFIG_URL}")
#             response = requests.get(CONFIG_URL)
#             response.raise_for_status()
#             config = yaml.safe_load(response.text)
        
#         # Save a local copy
#         with open(LOCAL_CONFIG_PATH, 'w') as f:
#             yaml.dump(config, f)
#         logger.info(f"Config saved to: {LOCAL_CONFIG_PATH}")
        
#         return config
    
#     except Exception as e:
#         logger.error(f"Failed to fetch config: {e}")
#         raise


# def deploy_via_rest_api(config: dict, dashboard_port: int = 8265):
#     """Deploy Ray Serve application using REST API."""
    
#     deploy_url = f"http://localhost:{dashboard_port}/api/serve/applications/"
    
#     logger.info(f"Deploying to Ray Serve via REST API: {deploy_url}")
#     logger.info("=" * 60)
    
#     try:
#         response = requests.put(
#             deploy_url,
#             json=config,
#             headers={"Content-Type": "application/json"}
#         )
        
#         if response.status_code == 200:
#             logger.info("✓ Application deployed successfully via REST API!")
#             return True
#         else:
#             logger.error(f"✗ Deployment failed: {response.status_code}")
#             logger.error(f"  Response: {response.text}")
#             return False
    
#     except requests.RequestException as e:
#         logger.error(f"✗ Failed to connect to Ray Serve: {e}")
#         return False


# def main():
#     try:
#         # Fetch configuration
#         config = fetch_config()
        
#         # Deploy using REST API
#         success = deploy_via_rest_api(config)
        
#         if success:
#             logger.info("\n" + "=" * 60)
#             logger.info("Deployment complete. Application is running.")
#             logger.info("Press Ctrl+C to exit (deployment will continue running)")
#             logger.info("=" * 60)
            
#             # Keep the script running to monitor (optional)
#             try:
#                 while True:
#                     import time
#                     time.sleep(1)
#             except KeyboardInterrupt:
#                 logger.info("\nExiting monitoring. Deployment continues in background.")
#         else:
#             logger.error("Deployment failed")
#             sys.exit(1)
    
#     except Exception as e:
#         logger.error(f"Error in main: {e}")
#         sys.exit(1)


# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         logger.info("\n\nReceived interrupt signal, shutting down...")
#         sys.exit(0)