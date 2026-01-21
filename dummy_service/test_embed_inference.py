from handlers.embedding_handler import EmbeddingClient
import asyncio
import yaml
from handlers.config_handler import ConfigurationClient
from handlers.auth_handler import AuthenticationClient
from handlers.handler_config_loader import HandlerConfigLoader
import asyncio
from pathlib import Path

loader_config = HandlerConfigLoader()
auth_config = loader_config.get_config(config_key="Authentication")
embedding_config = loader_config.get_config(config_key="Embedding")



async def main():
    embedd_client = EmbeddingClient(config=embedding_config)
    auth_client = AuthenticationClient(config=auth_config)

    token = await auth_client.get_token()
    print("token generated",type(token))
    await embedd_client.startup()
    
    text = "Helooooo"
    embedding = await embedd_client.sparse_bm25(["hello"], token=token)
    print(len(embedding[0]))

asyncio.run(main())