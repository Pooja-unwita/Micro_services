from ray import serve
from fastapi import FastAPI, HTTPException, Depends,Query
import logging
from numpy import ndarray
from vdb.models.models import SearchInput, SearchNamedCollectionInput, DeleteByFilenameInput,InsertResponse
from vdb.services.context import MilvusContext
from vdb.services.collection_creator import CollectionCreator
from vdb.services.index_manager import IndexManager
from vdb.services.crud_operator import CrudOperator
from vdb.services.search_operator import SearchOperator
from vdb.routers.token_verifier import verify_token
from vdb.models.models import CreateCollectionResponse, DropcollectionResponse, DeleteByFilenameResponse,SearchResponse,BulkDeleteResponse
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
        self.milvus_search = SearchOperator(self.ctx, self.index_manager)

    @app.post("/create_collection",response_model=CreateCollectionResponse)   
    async def create_collection(self, token: dict = Depends(verify_token)) -> dict:  
        try:     
            return await self.collection_creator.create_or_verify_collection(collection_name=self.ctx.collection_name, index_manager=self.index_manager)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Milvus failure create collection {str(e)}")
    

    @app.post("/create_collection/{collection_name}",response_model=CreateCollectionResponse)
    async def create_named_collection(self, collection_name: str, token: dict = Depends(verify_token)) -> bool:
        try:
            return await self.collection_creator.create_or_verify_collection(collection_name=collection_name, index_manager=self.index_manager)
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=f"Milvus failure check for the naming rules for collection {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Milvus failure check for the naming rules for collection  {str(e)}")

    @app.delete("/drop_collection", response_model=DropcollectionResponse)
    async def drop_collection(self) -> dict[str,str | bool]:
        try:
            if not await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
                raise HTTPException(status_code=404, detail="Collection not found")
            await self.crud.drop_collection(collection_name=self.ctx.collection_name)
            if await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
                raise HTTPException(status_code=500, detail="Failed to drop collection")
            return {"collection_name": self.ctx.collection_name, "drop_status": True}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=501,
                detail=f"Milvus failed to drop : {str(e)}"
            )          
        
    @app.delete("/drop_collection/{collection_name}", response_model=DropcollectionResponse)
    async def drop_named_collection(self, collection_name: str) -> dict[str,str | bool]:
        try:
            if await self.collection_creator.has_collection(collection_name=collection_name):
                await self.crud.drop_collection(collection_name=collection_name)
                if await self.collection_creator.has_collection(collection_name=collection_name):
                    raise HTTPException(status_code=500, detail="Failed to drop collection")
                return {"collection_name": collection_name, "drop_status": True}
            else:
                raise HTTPException(status_code=404, detail="Collection not found")  
        except HTTPException:
            raise
        except Exception as e:

            raise HTTPException(
                status_code=501,
                detail=f"Milvus failed to drop {collection_name}: {str(e)}"
            )          
 
             
    @app.post("/insert_documents", response_model=InsertResponse) #payload
    async def insert_documents(self, documents: list[dict] , token: dict = Depends(verify_token)) -> list: # if needed we can add validation
        try:
            if await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
                print("Inserting documents into collection:", self.ctx.collection_name)
                index_list = await self.index_manager.index_list(collection_name=self.ctx.collection_name)
                record_keys = documents[0].keys()
                
                if not all(col in record_keys for col in index_list):
                    raise HTTPException(status_code=400, detail="Document fields do not match collection schema")
                return await self.crud.insert(collection_name=self.ctx.collection_name, documents=documents) # {'insert_count': 2, 'ids': [464155119509574357, 464155119509574358],
            else:
                raise HTTPException(status_code=404, detail="Collection not found")
        except HTTPException:
            raise
        except Exception as e:

            raise HTTPException(
                status_code=502,
                detail=f"Milvus failed to insert document in : {str(e)}"
            )          



    @app.post("/insert_documents/{collection_name}", response_model=InsertResponse)
    async def insert_documents_named_collection(self, collection_name: str, documents: list[dict], token: dict = Depends(verify_token)) -> list:
        try:
            if not await self.collection_creator.has_collection(collection_name=collection_name):
                raise HTTPException(status_code=404, detail="Collection not found")
            index_list = await self.index_manager.index_list(collection_name=collection_name)
            record_keys = documents[0].keys()
            if not all(col in record_keys for col in index_list):
                    raise HTTPException(status_code=400, detail="Document fields do not match collection schema,sparse_vector mightnot provided")
            return await self.crud.insert(collection_name=collection_name, documents=documents)
        except HTTPException:
            raise
        except Exception as e:

            raise HTTPException(
                status_code=502,
                detail=f"Milvus failed to insert document in {collection_name}: {str(e)}"
            )          

    @app.post("/search", response_model=SearchResponse)
    async def search(self, search_input: SearchInput, token: dict = Depends(verify_token)) -> SearchResponse:
        if not await self.collection_creator.has_collection(self.ctx.collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")

        if self.ctx.Hybrid_search_flag and search_input.sparse_vector is None:
            raise HTTPException(status_code=400, detail="Hybrid search enabled but sparse_vector missing")

        if not self.ctx.Hybrid_search_flag and search_input.sparse_vector is not None:
            raise HTTPException(status_code=400, detail="Hybrid search disabled but sparse_vector provided")

        if search_input.top_k is None:
            search_input.top_k = self.ctx.top_k

        try:
            result = await self.milvus_search.search(
                collection_name=self.ctx.collection_name,
                dense_vecs=search_input.dense_vector,
                sparse_vec=search_input.sparse_vector,
                top_k=self.ctx.top_k,
                filter_expr=search_input.filter_expr
            )
            return SearchResponse(
                collection_name=self.ctx.collection_name,
                chunks=self.milvus_search.parse_milvus_results(result)
            )

        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Milvus failure to search document: {str(e)}"
            )

    @app.post("/search/{collection_name}", response_model=SearchResponse)
    async def search_named_collection(self, collection_name:str,search_input: SearchNamedCollectionInput, token: dict = Depends(verify_token)) -> SearchResponse:
        try:
            if not await self.collection_creator.has_collection(collection_name=collection_name):
                raise HTTPException(status_code=404, detail="Collection not found")
            
            if self.ctx.Hybrid_search_flag and search_input.sparse_vector is None:
                raise HTTPException(
                    status_code=400,
                    detail="Hybrid search is enabled but sparse_vector is not provided"
                )

            if not self.ctx.Hybrid_search_flag and search_input.sparse_vector is not None:
                raise HTTPException(
                    status_code=401,
                    detail="Hybrid search is disabled but sparse_vector was provided"
                )
            if not search_input.top_k:
                search_input.top_k = self.ctx.top_k
            # Use the unified search method
            result = await self.milvus_search.search(
                collection_name=collection_name,
                dense_vecs=search_input.dense_vector,
                sparse_vec=search_input.sparse_vector,
                top_k=search_input.top_k,
                filter_expr=search_input.filter_expr
            ) 
            return SearchResponse(collection_name=collection_name,
                                chunks=self.milvus_search.parse_milvus_results(raw_results=result))
        except HTTPException:
            raise

        except Exception as e:

            raise HTTPException(
                status_code=503,
                detail=f"Milvus failure to search document {collection_name}: {str(e)}"
            )
        
    @app.delete("/delete_by_ids")
    async def delete_by_ids(self, ids: list[int]=Query(...), token: dict = Depends(verify_token)) -> bool:
        try:
            if not await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
                raise HTTPException(status_code=404, detail="Collection not found")   
            return await self.crud.delete_by_ids(collection_name=self.ctx.collection_name, ids=ids)   
        except HTTPException:
            raise

        except Exception as e:

            raise HTTPException(
                status_code=504,
                detail=f"Milvus failed to delete by ids: {str(e)}"
            )          
 

    @app.delete("/delete_by_ids/{collection_name}")
    async def delete_by_ids_named_collection(self, collection_name: str, ids:list[int]=Query(...), 
                                             token: dict = Depends(verify_token)) -> bool:  
        try: 
            if not await self.collection_creator.has_collection(collection_name=collection_name):
                raise HTTPException(status_code=404, detail="Collection not found")
            return await self.crud.delete_by_ids(collection_name=collection_name, ids=ids)    
        except HTTPException:
            raise

        except Exception as e:

            raise HTTPException(
                status_code=504,
                detail=f"Milvus failed to delete by ids {collection_name}: {str(e)}"
            )          


    @app.delete("/delete_by_filename",response_model=BulkDeleteResponse)
    async def delete_by_filename(self,filename:list[str]= Query(...), token: dict = Depends(verify_token)) -> dict :
        try:
            if not await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
                raise HTTPException(status_code=404, detail="Collection not found")  
            return await self.crud.delete_by_filename(collection_name=self.ctx.collection_name, filename=filename, field_name=self.ctx.deletion_field_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Milvus failed to delete by filenames{str(e)}")
  

    @app.delete("/delete_by_filename/{collection_name}",response_model=BulkDeleteResponse)
    async def delete_by_filename_named_collection(self, collection_name:str,filename:list[str]= Query(...), token: dict = Depends(verify_token)) -> bool  :  
        if not await self.collection_creator.has_collection(collection_name=collection_name):
            raise HTTPException(status_code=404, detail="Collection not found") 
        return await self.crud.delete_by_filename(collection_name=collection_name, filename=filename, field_name=self.ctx.deletion_field_name)
    
    @app.delete("/delete_by_json",response_model=BulkDeleteResponse)
    async def delete_by_json_field(self,filename:list[str]= Query(...), token: dict = Depends(verify_token)) -> BulkDeleteResponse  :
        try:  
            if not await self.collection_creator.has_collection(collection_name=self.ctx.collection_name):
                raise HTTPException(status_code=404, detail="Collection not found") 
            response=await self.crud.delete_by_json_field(collection_name=self.ctx.collection_name,field_name=self.ctx.deletion_field_name,key="filename",values=filename)#self.ctx.deletion_field_name)
            response["collection_name"] = self.ctx.collection_name
            return response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=505,
                detail=f"Milvus failed to delete by json field: {str(e)}"
            )          

    
    @app.delete("/delete_by_json/{collection_name}",response_model=BulkDeleteResponse)
    async def delete_by_json_field(self, collection_name:str,filename:list[str]= Query(...), 
                                   token: dict = Depends(verify_token)) -> BulkDeleteResponse  : 
        try: 
            if not await self.collection_creator.has_collection(collection_name=collection_name):
                raise HTTPException(status_code=404, detail="Collection not found") 
            response = await self.crud.delete_by_json_field(collection_name=collection_name,field_name=self.ctx.deletion_field_name,key="filename",values=filename)#self.ctx.deletion_field_name)
            response["collection_name"] = collection_name
            return response
        except HTTPException:
            raise

        except Exception as e:

            raise HTTPException(
                status_code=505,
                detail=f"Milvus failed to delete by json field {collection_name}: {str(e)}"
            )          


    
