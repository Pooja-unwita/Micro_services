from ray import serve
from fastapi import FastAPI, HTTPException
import logging

from vdb.services.context import MilvusContext
from vdb.services.collection_creator import CollectionCreator
from vdb.services.index_manager import IndexManager
from vdb.services.crud_operator import CrudOperator
from vdb.services.search_operator import SearchOperator


logger = logging.getLogger(__name__)

app = FastAPI(title="Milvus Vector Service")

@serve.deployment
@serve.ingress(app)
class MilvusService:
    def __init__(self, milvus_config: dict):
        """
        Runs ONCE per Ray Serve replica
        """
        self.ctx = MilvusContext(milvus_config)

        self.index_manager = IndexManager(self.ctx)
        self.collection_creator = CollectionCreator(self.ctx)
        self.crud = CrudOperator(self.ctx)
        self.search = SearchOperator(self.ctx, self.index_manager)

    @app.post("/create_collection")   
    async def create_collection(self) -> bool:        
        return await self.collection_creator.create_or_verify_collection(collection_name=self.ctx.collection_name, index_manager=self.index_manager)
    
    @app.post("/create_collection/{collection_name}")
    async def create_named_collection(self, collection_name: str) -> bool:
        try:
            return await self.collection_creator.create_or_verify_collection(collection_name=collection_name, index_manager=self.index_manager)
    
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/drop_collection")
    async def drop_collection(self) -> bool:
        return await self.crud.drop_collection(collection_name=self.ctx.collection_name)
    
    @app.delete("/drop_collection/{collection_name}")
    async def drop_named_collection(self, collection_name: str) -> bool:
        return await self.crud.drop_collection(collection_name=collection_name) 
    
    
