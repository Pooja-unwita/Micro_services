from ray import serve
from fastapi import FastAPI
from ray.serve.handle import DeploymentHandle
from Embedding_Service.models.embed_input import EmbedInput
from Embedding_Service.routers.auth import app as auth_router
from fastapi import FastAPI, Depends
from Embedding_Service.routers.auth import  verify_token
import os

# # ray.init(
# #     ignore_reinit_error=True,
# #     include_dashboard=False
# # )

app = FastAPI()
app.include_router(auth_router)

@serve.deployment
@serve.ingress(app)
class EmbeddingService:
    def __init__(self, query_vectorizer:DeploymentHandle, text_vectorizer:DeploymentHandle , sparse_vectorizer:DeploymentHandle):
        self.query_vectorizer = query_vectorizer
        self.text_vectorizer = text_vectorizer
        self.sparse_vectorizer = sparse_vectorizer


    @app.post("/dense/query")
    async def embed_query(self, text: EmbedInput, token: dict = Depends(verify_token)):
        return await self.query_vectorizer.embed.remote(text)
    
    @app.post("/sparse/bm25")
    async def embed_bm25(self, text: EmbedInput, token: dict = Depends(verify_token)):
        return await self.sparse_vectorizer.bm25_vectorise_text.remote(text)
    
    @app.post("/sparse/splade")
    async def embed_splade(self, text: EmbedInput, token: dict = Depends(verify_token)):
        print("hi")
        return await self.sparse_vectorizer.build_splade_embeddings.remote(text)

    @app.post("/sparse/tfidf")
    async def embed_tfidf(self, text: EmbedInput, token: dict = Depends(verify_token)):
        return await self.sparse_vectorizer.build_TFIDF_embeddings.remote(text)

    @app.post("/dense/text")
    async def embed_text(self, text: EmbedInput, token: dict = Depends(verify_token)):
        return await self.text_vectorizer.embed.remote(text)
 