from handlers.embedding_handler import EmbeddingClient
from handlers.auth_handler import AuthenticationClient
import asyncio
import yaml
from handlers.handler_config_loader import ConfigLoader

config_loader = ConfigLoader()
embedding_config = config_loader.get_config("Embedding")
auth_config = config_loader.get_config("Authentication")
print(auth_config)

embedd_client = EmbeddingClient(config=embedding_config)
auth_client = AuthenticationClient(config=auth_config)

async def main():

    token = await auth_client.get_token()
    print("token generated",type(token))
    await embedd_client.startup()

    text = "Helooooo"
    embedding = await embedd_client.dense_text(["hello"], token=token)
    print(len(embedding[0]))

asyncio.run(main())