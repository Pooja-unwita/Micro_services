from ray import serve
from fastapi import FastAPI, HTTPException
import logging
from numpy import ndarray
from vdb.models.models import SearchInput, SearchNamedCollectionInput, DeleteByFilenameInput
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
        if not await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")
        return await self.crud.drop_collection(collection_name=self.ctx.collection_name)
    

    @app.delete("/drop_collection/{collection_name}")
    async def drop_named_collection(self, collection_name: str) -> bool:
        if await self.collection_creator.has_collection(collection_name=collection_name):
            return await self.crud.drop_collection(collection_name=collection_name) 
        else:
            raise HTTPException(status_code=404, detail="Collection not found")
    

    @app.post("/insert_documents")
    async def insert_documents(self, documents: list[dict]) -> list:
       
        if await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
            print("Inserting documents into collection:", self.ctx.collection_name)
            index_list = await self.index_manager.index_list(collection_name=self.ctx.collection_name)
            record_keys = documents[0].keys()
            
            if not all(col in record_keys for col in index_list):
                raise HTTPException(status_code=400, detail="Document fields do not match collection schema")
            return await self.crud.insert(collection_name=self.ctx.collection_name, documents=documents)
        else:
            raise HTTPException(status_code=404, detail="Collection not found")


    @app.post("/insert_documents/{collection_name}")
    async def insert_documents_named_collection(self, collection_name: str, documents: list[dict]) -> list:
        if not await self.collection_creator.has_collection(collection_name=collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")
        index_list = await self.index_manager.index_list(collection_name=collection_name)
        record_keys = documents[0].keys()
        if not all(col in record_keys for col in index_list):
                raise HTTPException(status_code=400, detail="Document fields do not match collection schema")
        return await self.crud.insert(collection_name=collection_name, documents=documents)

    @app.post("/search", response_model=None)
    async def search(self, search_input: SearchInput) -> list:
        # Check if collection exists
        if not await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Validate search parameters based on hybrid search flag
        if self.ctx.Hybrid_search_flag and search_input.sparse_vector is None:
            raise HTTPException(
                status_code=400,
                detail="Hybrid search is enabled but sparse_vector is not provided"
            )

        if not self.ctx.Hybrid_search_flag and search_input.sparse_vector is not None:
            raise HTTPException(
                status_code=400,
                detail="Hybrid search is disabled but sparse_vector was provided"
            )
        if not search_input.top_k:
            search_input.top_k = self.ctx.top_k
        # Use the unified search method
        return await self.search.search(
            collection_name=self.ctx.collection_name,
            dense_vecs=search_input.dense_vector,
            sparse_vec=search_input.sparse_vector,
            top_k=search_input.top_k,
            filter_expr=search_input.filter_expr
        )

    @app.post("/search/{collection_name}", response_model=None)
    async def search_named_collection(self, search_input: SearchNamedCollectionInput) -> list:
        # Check if collection exists
        if not await self.collection_creator.has_collection(collection_name=search_input.collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Validate search parameters based on hybrid search flag
        if self.ctx.Hybrid_search_flag and search_input.sparse_vector is None:
            raise HTTPException(
                status_code=400,
                detail="Hybrid search is enabled but sparse_vector is not provided"
            )

        if not self.ctx.Hybrid_search_flag and search_input.sparse_vector is not None:
            raise HTTPException(
                status_code=400,
                detail="Hybrid search is disabled but sparse_vector was provided"
            )
        if not search_input.top_k:
            search_input.top_k = self.ctx.top_k
        # Use the unified search method
        return await self.search.search(
            collection_name=search_input.collection_name,
            dense_vecs=search_input.dense_vector,
            sparse_vec=search_input.sparse_vector,
            top_k=search_input.top_k,
            filter_expr=search_input.filter_expr
        )  
    
    @app.delete("/delete_by_ids")
    async def delete_by_ids(self, ids: list) -> bool:
        if not await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")   
        return await self.crud.delete_by_ids(collection_name=self.ctx.collection_name, ids=ids)    


    @app.delete("/delete_by_ids/{collection_name}")
    async def delete_by_ids_named_collection(self, collection_name: str, ids: list) -> bool:   
        if not await self.collection_creator.has_collection(collection_name=collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")
        return await self.crud.delete_by_ids(collection_name=collection_name, ids=ids)    


    @app.delete("/delete_by_filename")
    # async def delete_by_filename(self,payload: DeleteByFilenameInput) -> bool  : 
    async def delete_by_filename(self,filename:str, field_name: str = "metadata") -> bool  :
        if not await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")  
        return await self.crud.delete_by_filename(collection_name=self.ctx.collection_name, filename=filename, field_name=field_name)
    

    @app.delete("/delete_by_filename/{collection_name}")
    async def delete_by_filename_named_collection(self, collection_name: str, filename: str, field_name: str) -> bool  :  
        if not await self.collection_creator.has_collection(collection_name=collection_name):
            raise HTTPException(status_code=404, detail="Collection not found") 
        return await self.crud.delete_by_filename(collection_name=collection_name, filename=filename, field_name=field_name)
    
def milvus_service_builder(args):
    return MilvusService.bind(milvus_config= args["milvus_config"])