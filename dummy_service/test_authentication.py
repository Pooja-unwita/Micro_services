from handlers.config_handler import ConfigurationClient
from handlers.auth_handler import AuthenticationClient
from handlers.handler_config_loader import HandlerConfigLoader
import asyncio
from pathlib import Path
ISSUER = "Auth_Service"
AUDIENCE = "FE_Service"
loader_config = HandlerConfigLoader()
auth_config = loader_config.get_config(config_key="Authentication")
print(auth_config)

async def main():
    auth_client =AuthenticationClient(config=auth_config)
    await auth_client.startup()
    token=await auth_client.get_token()
    
    print(f"Obtained Token: {token}")
    await auth_client.verify_token(token=token,issuer=ISSUER,audience=AUDIENCE)
asyncio.run(main())