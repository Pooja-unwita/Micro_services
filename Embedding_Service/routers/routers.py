from ray import serve
from fastapi import FastAPI
from ray.serve.handle import DeploymentHandle
from Embedding_Service.models.models import EmbedInput
#from Embedding_Service.routers.token_verifier import app as auth_router
from fastapi import FastAPI, Depends
from Embedding_Service.routers.token_verifier import verify_token
import os

app = FastAPI()
#app.include_router(auth_router)

@serve.deployment
@serve.ingress(app)
class EmbeddingService:
    """
    Docstring for EmbeddingService
    """
    def __init__(self, query_vectorizer:DeploymentHandle,
                  text_vectorizer:DeploymentHandle , sparse_vectorizer:DeploymentHandle):
        """
        Docstring for __init__
        
        :param self: Description
        :param query_vectorizer: Description
        :type query_vectorizer: DeploymentHandle
        :param text_vectorizer: Description
        :type text_vectorizer: DeploymentHandle
        :param sparse_vectorizer: Description
        :type sparse_vectorizer: DeploymentHandle
        """
        self.query_vectorizer = query_vectorizer
        self.text_vectorizer = text_vectorizer
        self.sparse_vectorizer = sparse_vectorizer


    @app.post("/dense/query")
    async def embed_query(self, text: EmbedInput, token: dict = Depends(verify_token)):
        try:
            return await self.query_vectorizer.embed.remote(text)
        except Exception as e:
            raise e
    
    @app.post("/sparse/bm25")
    async def embed_bm25(self, text: EmbedInput, token: dict = Depends(verify_token)):
        try:
            return await self.sparse_vectorizer.bm25_vectorise_text.remote(text)
        except Exception as e:
            raise e
    
    @app.post("/sparse/splade")
    async def embed_splade(self, text: EmbedInput, token: dict = Depends(verify_token)):
        try:
            return await self.sparse_vectorizer.build_splade_embeddings.remote(text)
        except Exception as e:
            raise e

    @app.post("/sparse/tfidf")
    async def embed_tfidf(self, text: EmbedInput, token: dict = Depends(verify_token)):
        try:
            return await self.sparse_vectorizer.build_TFIDF_embeddings.remote(text)
        except Exception as e:
            raise e

    @app.post("/dense/text")
    async def embed_text(self, text: EmbedInput, token: dict = Depends(verify_token)):
        try:
            return await self.text_vectorizer.embed.remote(text)
        except Exception as e:
            raise e
 