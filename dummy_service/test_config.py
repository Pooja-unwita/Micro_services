from handlers.config_handler import ConfigurationClient
from handlers.auth_handler import AuthenticationClient
from handlers.handler_config_loader import HandlerConfigLoader
import asyncio
from pathlib import Path

loader_config = HandlerConfigLoader()
config_config = loader_config.get_config(config_key="Configuration")
auth_config = loader_config.get_config(config_key="Authentication")
print(auth_config)

async def main():
    auth_client =AuthenticationClient(config=auth_config)
    token=await auth_client.get_token()
    
    config_client = ConfigurationClient(config=config_config)
    await config_client.startup()
    cluster_dict, filepath = await config_client.fetch_config(service_name="Ray_Cluster", token=token)
    
    await config_client.save_yaml(data=cluster_dict, output_dir = Path(__file__).parent, filename=filepath)
    # path = await config_client.get_config_file("Ray_Cluster", token=token, output_path=Path(__file__).parent)
    # print(f"Config file saved at: {filepath}")
    # print(cluster_dict)
    await config_client.shutdown()

asyncio.run(main())