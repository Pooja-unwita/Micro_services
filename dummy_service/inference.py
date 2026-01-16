from embedding_handler import EmbeddingClient
from auth_handler import AuthenticationClient
import asyncio


embedd_client = EmbeddingClient()
auth_client = AuthenticationClient()

async def main():

    token = await auth_client.get_token()
    print("token generated",type(token))
    await embedd_client.startup()

    text = "Helooooo"
    embedding = await embedd_client.dense_text(["hello"], token=token)
    print(len(embedding))

asyncio.run(main())