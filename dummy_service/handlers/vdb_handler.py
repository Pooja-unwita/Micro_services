import asyncio
import httpx
from utils.set_attribute import AttributeSetter


class VDBHandler:

    def __init__(self, config:dict):
        AttributeSetter.set_attributes(self, config)
        self.client: httpx.AsyncClient = None

    async def startup(self):
        try:
            if self.client is None:
                self.client = httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=self.timeout,
                    headers=self.headers,
                    limits=httpx.Limits(
                        max_connections=self.http_limits["max_connections"],
                        max_keepalive_connections=self.http_limits["max_keepalive_connections"],
                    )
                )            
        except Exception as e:
            raise e


    async def shutdown(self):
        """Close the connection pool gracefully."""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
        except Exception as e:
            raise e
        
    async def create_collection(self):
        try:
            response = await self.client.post("/create_collection")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to create collection: {e}")
        
    async def create_named_collection(self, collection_name: str):
        try:
            response = await self.client.post(f"/create_collection/{collection_name}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to create collection '{collection_name}': {e}")
        
    async def drop_collection(self):
        try:
            response = await self.client.delete("/drop_collection")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to drop collection: {e}")
        
    async def drop_named_collection(self, collection_name: str):
        try:
            response = await self.client.delete(f"/drop_collection/{collection_name}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to drop collection '{collection_name}': {e}")
        
    async def insert_documents(self, documents: list[dict]):
        try:
            response = await self.client.post("/insert_documents", json=documents)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to insert documents: {e}")
        
    async def insert_documents_named_collection(self, collection_name: str, documents: list[dict]):
        try:
            response = await self.client.post(f"/insert_documents/{collection_name}", json=documents)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to insert documents into collection '{collection_name}': {e}")

    async def search(
    self,
    dense_vecs: list[list[float]],
    sparse_vec: list[dict] | None = None,
    top_k: int | None = None,
    filter_expr: str | None = None
    ):
        try:
            response = await self.client.post(
                "/search",
                json={
                    "dense_vector": dense_vecs,
                    "sparse_vector": sparse_vec,
                    "top_k": top_k,
                    "filter_expr": filter_expr
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to perform search: {e}")
    
    # async def search(self,dense_vecs: list,sparse_vec: list | None = None,top_k: int | None = None,filter_expr: str | None = None):
    #     try:
    #         response = await self.client.get("/search", json={
    #             "dense_vectors": dense_vecs,
    #             "sparse_vector": sparse_vec,
    #             "top_k": top_k,
    #             "filter_expr": filter_expr
    #         })
    #         response.raise_for_status()
    #         return response.json()
    #     except httpx.HTTPError as e:
    #         raise RuntimeError(f"Failed to perform search: {e}")
        
    async def search_named_collection(self, collection_name: str, dense_vecs: list[list[float]],sparse_vec: list | None = None,top_k: int | None = None,filter_expr: str | None = None):
        try:
            response = await self.client.post(f"/search/{collection_name}", json={
                "collection_name": collection_name,
                "dense_vector": dense_vecs, 
                "sparse_vector": sparse_vec,
                "top_k": top_k, 
                "filter_expr": filter_expr
            })
            response.raise_for_status()         
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to perform search on collection '{collection_name}': {e}")
        

    async def delete_documents_by_filename(self, filename, field_name="metadata"):
        try:
            response = await self.client.delete("/delete_by_filename", params={
                "filename": filename,
                "field_name": field_name
            })
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to delete documents by filename '{filename}': {e}")
