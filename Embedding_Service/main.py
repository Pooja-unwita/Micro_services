import subprocess
import sys
import asyncio
from Handlers.config_handler import ConfigurationClient
import os
import time

CALLER="embedding_service"

# CONFIG_URL = r"C:\Users\hp\Downloads\Embedding\Embedding\Configuration_service\embed.yaml"
# LOCAL_CONFIG_PATH = "embed_runtime.yaml"  # Temporary local copy


async def fetch_config() -> dict:
    """Fetch configuration from config service (or local file)."""
    # For now, reading from local file
    # In production, you could fetch from a remote config service:
    # response = requests.get("http://config-service:8080/embed.yaml")
    # config = yaml.safe_load(response.text)
    
    config_client = ConfigurationClient(caller=CALLER)
    await config_client.startup()
    config_path = await config_client.get_config_file("Embedding_Service")
    await config_client.shutdown()
    return config_path


def run_serve_cli(config_path: str):
    """Run 'serve run' CLI command with the config file."""
    
    print(f"\nStarting Ray Serve with: serve run {config_path}")
    print("="*60)
    
    try:
        # Run the serve command - this will block until interrupted
        # Use --blocking flag to keep the process running

        # cmd = ["serve", "deploy", config_path, "--blocking", "--app-dir", "."]
        # process=subprocess.run(cmd, check=True,stdout=sys.stdout,
        #     stderr=sys.stderr)

        process = subprocess.run(
            ["serve", "run", config_path],
            check=True,
            # Don't capture output - let it stream to console
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Serve command failed with exit code {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✓ Received interrupt signal, shutting down...")
        sys.exit(0)


async def main():
    print("="*60)
    print("Embedding Service Launcher")
    print("="*60)
    
    # 1. Fetch configuration
    print("\n[1/3] Fetching configuration...")
    config_path = await fetch_config()
    
    # 3. Run serve CLI
    print(f"\n[3/3] Deploying service...")
    run_serve_cli(config_path=config_path)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✓ Received interrupt signal, exiting...")






####################################################################################################################

# import ray
# from ray import serve
# import yaml
# import time
# import requests
# import asyncio

# # CONFIG_URL = r"C:\Users\hp\Downloads\Embedding\Embedding\Configuration_service\embed.yaml"


# async def fetch_config() -> dict:
#     """Fetch configuration from config service (or local file)."""
#     # For now, reading from local file
#     # In production, you could fetch from a remote config service:
#     # response = requests.get("http://config-service:8080/embed.yaml")
#     # config = yaml.safe_load(response.text)
    
#     config_client = ConfigurationClient()
#     await config_client.startup()
#     config_path = await config_client.get_config_file("Embedding_Service")
#     await config_client.shutdown()
#     with open(config_path, 'r') as f:
#         data = yaml.safe_load(f)
#     return data



# def deploy_via_rest_api(config: dict, dashboard_port: int = 8266):
#     """Deploy Ray Serve application using REST API."""
    
#     # Prepare the deployment request
#     deploy_url = f"http://localhost:{dashboard_port}/api/serve/applications/"
    
#     # The REST API expects the config in a specific format
#     response = requests.put(
#         deploy_url,
#         json=config,
#         headers={"Content-Type": "application/json"}
#     )
    
#     if response.status_code == 200:
#         print("✓ Application deployed successfully via REST API!")
#         return True
#     else:
#         print(f"✗ Deployment failed: {response.status_code}")
#         print(f"  Response: {response.text}")
#         return False


# async def main():
#     # 1. Fetch configuration
#     print("Fetching configuration...")
#     config = await fetch_config()
    
#     # 2. Initialize Ray (if not already running)
#     # Note: In production, Ray cluster should already be running
#     if not ray.is_initialized():
#         print("I am iitialising")
#         ray.init(ignore_reinit_error=True)
    
#     # 3. Start Ray Serve with global config
#     print("Starting Ray Serve...")
#     # serve.start(
#     #     proxy_location=config.get('proxy_location', 'EveryNode'),
#     #     http_options=config.get('http_options', {}),
#     #     logging_config=config.get('logging_config', {})
#     # )
    
#     # 4. Deploy application via REST API
#     print("Deploying application...")
    
#     # Give Ray Dashboard a moment to start
#     time.sleep(2)
    
#     success = deploy_via_rest_api(config)
    
#     if success:
#         http_opts = config.get('http_options', {})
#         host = http_opts.get('host', 'localhost')
#         port = http_opts.get('port', 8001)
#         app_name = config['applications'][0]['name']
        
#         print(f"\n{'='*60}")
#         print(f"✓ {app_name} is now running!")
#         print(f"  HTTP endpoint: http://{host}:{port}")
#         print(f"  Dashboard: http://localhost:8265")
#         print(f"{'='*60}\n")
        
#         # Keep the service running
#         try:
#             print("Service is running. Press Ctrl+C to stop...")
#             while True:
#                 time.sleep(3600)
#         except KeyboardInterrupt:
#             print("\n\nShutting down Ray Serve...")
#             serve.shutdown()
#             ray.shutdown()
#             print("✓ Shutdown complete")
#     else:
#         print("Deployment failed. Check the error messages above.")
#         serve.shutdown()


# if __name__ == "__main__":
#     asyncio.run(main())