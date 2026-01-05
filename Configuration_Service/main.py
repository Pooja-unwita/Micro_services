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
            ["serve", "deploy", config_path],
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
 