# import asyncio
# import httpx
# from utils.set_attribute import AttributeSetter


# class VDBHandler:

#     def __init__(self, config:dict):
#         AttributeSetter.set_attributes(self, config)
#         self.client: httpx.AsyncClient = None
#         self.semaphore = asyncio.Semaphore(self.max_concurrency)


#     async def startup(self):
#         try:
#             if self.client is None:
#                 self.client = httpx.AsyncClient(
#                     base_url=self.base_url,
#                     timeout=self.timeout,
#                     headers=self.headers,
#                     limits=httpx.Limits(
#                         max_connections=self.http_limits["max_connections"],
#                         max_keepalive_connections=self.http_limits["max_keepalive_connections"],
#                     )
#                 )            
#         except Exception as e:
#             raise e


#     async def shutdown(self):
#         """Close the connection pool gracefully."""
#         try:
#             if self.client:
#                 await self.client.aclose()
#                 self.client = None
#         except Exception as e:
#             raise e
    
#     async def _post(self, path: str, payload: dict, token:str):
#         """Send POST request and handle 401 token refresh."""
        
#         try:
#             if not self.client:
#                 await self.startup()
#         except Exception as e:
#             raise e

#         async with self.semaphore:
#             try:
#                 _headers = {
#                     **self.headers,
#                     "Authorization": f"Bearer {token}",
#                     }
                
#                 response = await self.client.post(path, json=payload, headers=_headers)
#                 response.raise_for_status()
#                 return response.json()

#             except httpx.HTTPStatusError as e:
                
#                 raise RuntimeError(
#                     f"HTTP {e.response.status_code} from {path}: {e.response.text}"
#                 ) from e

#             except httpx.RequestError as e:
#                 raise RuntimeError(
#                     f"Error contacting {self.base_url}{path}: {e}"
#                 ) from e

        
#     async def create_collection(self):
#         try:
#             response = await self.client.post("/create_collection")
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPError as e:
#             raise RuntimeError(f"Failed to create collection: {e}")
        
#     async def create_named_collection(self, collection_name: str):
#         try:
#             response = await self.client.post(f"/create_collection/{collection_name}")
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPError as e:
#             raise RuntimeError(f"Failed to create collection '{collection_name}': {e}")
        
#     async def drop_collection(self):
#         try:
#             response = await self.client.delete("/drop_collection")
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPError as e:
#             raise RuntimeError(f"Failed to drop collection: {e}")
        
#     async def drop_named_collection(self, collection_name: str):
#         try:
#             response = await self.client.delete(f"/drop_collection/{collection_name}")
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPError as e:
#             raise RuntimeError(f"Failed to drop collection '{collection_name}': {e}")
        
#     async def insert_documents(self, documents: list[dict]):
#         try:
#             response = await self.client.post("/insert_documents", json=documents)
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPError as e:
#             raise RuntimeError(f"Failed to insert documents: {e}")
        
#     async def insert_documents_named_collection(self, collection_name: str, documents: list[dict]):
#         try:
#             response = await self.client.post(f"/insert_documents/{collection_name}", json=documents)
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPError as e:
#             raise RuntimeError(f"Failed to insert documents into collection '{collection_name}': {e}")

#     async def search(
#     self,
#     dense_vecs: list[list[float]],
#     sparse_vec: list[dict] | None = None,
#     top_k: int | None = None,
#     filter_expr: str | None = None
#     ):
#         try:
#             response = await self.client.post(
#                 "/search",
#                 json={
#                     "dense_vector": dense_vecs,
#                     "sparse_vector": sparse_vec,
#                     "top_k": top_k,
#                     "filter_expr": filter_expr
#                 }
#             )
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPError as e:
#             raise RuntimeError(f"Failed to perform search: {e}")
    
#     # async def search(self,dense_vecs: list,sparse_vec: list | None = None,top_k: int | None = None,filter_expr: str | None = None):
#     #     try:
#     #         response = await self.client.get("/search", json={
#     #             "dense_vectors": dense_vecs,
#     #             "sparse_vector": sparse_vec,
#     #             "top_k": top_k,
#     #             "filter_expr": filter_expr
#     #         })
#     #         response.raise_for_status()
#     #         return response.json()
#     #     except httpx.HTTPError as e:
#     #         raise RuntimeError(f"Failed to perform search: {e}")
        
#     async def search_named_collection(self, collection_name: str, dense_vecs: list[list[float]],sparse_vec: list | None = None,top_k: int | None = None,filter_expr: str | None = None):
#         try:
#             response = await self.client.post(f"/search/{collection_name}", json={
#                 "collection_name": collection_name,
#                 "dense_vector": dense_vecs, 
#                 "sparse_vector": sparse_vec,
#                 "top_k": top_k, 
#                 "filter_expr": filter_expr
#             })
#             response.raise_for_status()         
#             return response.json()
#         except httpx.HTTPError as e:
#             raise RuntimeError(f"Failed to perform search on collection '{collection_name}': {e}")
        

#     async def delete_documents_by_filename(self, filename, field_name="metadata"):
#         try:
#             response = await self.client.delete("/delete_by_filename", params={
#                 "filename": filename,
#                 "field_name": field_name
#             })
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPError as e:
#             raise RuntimeError(f"Failed to delete documents by filename '{filename}': {e}")
import asyncio
import httpx
from utils.set_attribute import AttributeSetter

class VDBHandler:
    def __init__(self, config: dict):
        AttributeSetter.set_attributes(self, config)
        self.client: httpx.AsyncClient = None
        self.semaphore = asyncio.Semaphore(self.max_concurrency)

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

    async def _post(self, path: str, payload: dict, token: str):
        """Send POST request and handle 401 token refresh."""
        try:
            if not self.client:
                await self.startup()
        except Exception as e:
            raise e
        
        async with self.semaphore:
            try:
                _headers = {
                    **self.headers,
                    "Authorization": f"Bearer {token}",
                }
                response = await self.client.post(path, json=payload, headers=_headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise RuntimeError(
                    f"HTTP {e.response.status_code} from {path}: {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                raise RuntimeError(
                    f"Error contacting {self.base_url}{path}: {e}"
                ) from e

    async def create_collection(self, token: str):
        try:
            response = await self._post("/create_collection", {}, token)
            return response
        except RuntimeError as e:
            raise RuntimeError(f"Failed to create collection: {e}") from e

    async def create_named_collection(self, collection_name: str, token: str):
        try:
            response = await self._post(f"/create_collection/{collection_name}", {}, token)
            return response
        except RuntimeError as e:
            raise RuntimeError(f"Failed to create collection '{collection_name}': {e}") from e

    async def drop_collection(self, token: str):
        try:
            if not self.client:
                await self.startup()
            
            async with self.semaphore:
                _headers = {
                    **self.headers,
                    "Authorization": f"Bearer {token}",
                }
                response = await self.client.delete("/drop_collection", headers=_headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to drop collection: {e}") from e

    async def drop_named_collection(self, collection_name: str, token: str):
        try:
            if not self.client:
                await self.startup()
            
            async with self.semaphore:
                _headers = {
                    **self.headers,
                    "Authorization": f"Bearer {token}",
                }
                response = await self.client.delete(f"/drop_collection/{collection_name}", headers=_headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to drop collection '{collection_name}': {e}") from e

    async def insert_documents(self, documents: list[dict], token: str):
        try:
            response = await self._post("/insert_documents", documents, token)
            return response
        except RuntimeError as e:
            raise RuntimeError(f"Failed to insert documents: {e}") from e

    async def insert_documents_named_collection(self, collection_name: str, documents: list[dict], token: str):
        try:
            response = await self._post(f"/insert_documents/{collection_name}", documents, token)
            return response
        except RuntimeError as e:
            raise RuntimeError(f"Failed to insert documents into collection '{collection_name}': {e}") from e

    async def search(
        self,
        dense_vecs: list[list[float]],
        token: str,
        sparse_vec: list[dict] | None = None,
        top_k: int | None = None,
        filter_expr: str | None = None
    ):
        try:
            payload = {
                "dense_vector": dense_vecs,
                "sparse_vector": sparse_vec,
                "top_k": top_k,
                "filter_expr": filter_expr
            }
            response = await self._post("/search", payload, token)
            return response
        except RuntimeError as e:
            raise RuntimeError(f"Failed to perform search: {e}") from e

    async def search_named_collection(
        self,
        collection_name: str,
        dense_vecs: list[list[float]],
        token: str,
        sparse_vec: list | None = None,
        top_k: int | None = None,
        filter_expr: str | None = None
    ):
        try:
            payload = {
                "collection_name": collection_name,
                "dense_vector": dense_vecs,
                "sparse_vector": sparse_vec,
                "top_k": top_k,
                "filter_expr": filter_expr
            }
            response = await self._post(f"/search/{collection_name}", payload, token)
            return response
        except RuntimeError as e:
            raise RuntimeError(f"Failed to perform search on collection '{collection_name}': {e}") from e

    async def delete_documents_by_filename(self, filename: str, token: str, field_name: str = "metadata"):
        try:
            if not self.client:
                await self.startup()
            
            async with self.semaphore:
                _headers = {
                    **self.headers,
                    "Authorization": f"Bearer {token}",
                }
                response = await self.client.delete(
                    "/delete_by_filename",
                    params={"filename": filename, "field_name": field_name},
                    headers=_headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to delete documents by filename '{filename}': {e}") from e