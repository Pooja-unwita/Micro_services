import asyncio
import logging
from typing import List, Optional
import httpx
from contextvars import ContextVar

# current_token = ContextVar('jwt_token')

class EmbeddingClient:
    """
    High-performance async HTTP client for communicating with the Embedding Service.
    Intended to be reused inside Ray Serve deployments.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8001/embed",
        max_concurrency: int = 100,
    ):

        """
        Args:
            service_name: The name of the service to authenticate as.
            secret_key: The secret key for the service.
            base_url: The base URL of the embedding service.
            max_concurrency: Maximum number of parallel requests.
        """
        self.base_url = base_url
        
        self.client: Optional[httpx.AsyncClient] = None
        self._headers = {"Content-Type": "application/json"}
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self._token_lock = asyncio.Lock() # To prevent multiple simultaneous token refreshes


    async def startup(self):
        try:
            if self.client is None:

                self.client = httpx.AsyncClient(
                                base_url=self.base_url,
                                timeout=httpx.Timeout(None),
                                limits=httpx.Limits(
                                    max_connections=100,
                                    max_keepalive_connections=20,
                                ),
                                headers=self._headers,
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


    async def _post(self, path: str, payload: dict, token:str):
        """Send POST request and handle 401 token refresh."""
        
        try:
            if not self.client:
                await self.startup()
        except Exception as e:
            raise e

        async with self.semaphore:
            try:
                headers = {
                    **self._headers,
                    "Authorization": f"Bearer {token}",
                    }
                
                response = await self.client.post(path, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                # if e.response.status_code == 401:
                #     # Token is invalid, force refresh
                #     logging.warning("Auth token expired, refreshing token...")
                    
                #     async with self._token_lock:
                #         # Clear the invalid token
                #         current_token.delete()
                #         # Get fresh token
                #         token = await self.get_token()
                    
                #     # Retry once with new token
                #     params = {"token": token}
                #     response = await self.client.post(path, json=payload, params=params)
                #     response.raise_for_status()
                #     return response.json()
                
                raise RuntimeError(
                    f"HTTP {e.response.status_code} from {path}: {e.response.text}"
                ) from e

            except httpx.RequestError as e:
                raise RuntimeError(
                    f"Error contacting {self.base_url}{path}: {e}"
                ) from e
            
    
    async def dense_text(self, texts: List[str], token:str):
        try:
            return await self._post("/dense/text", {"text": texts}, token=token)
        except Exception as e:
            raise e

    async def dense_query(self, texts: List[str], token:str):
        try:
            return await self._post("/dense/query", {"text": texts}, token=token)
        except Exception as e:
            raise e

    async def sparse_splade(self, texts: List[str], token):
        try:
            return await self._post("/sparse/splade", {"text": texts}, token=token)
        except Exception as e:
            raise e

    async def sparse_bm25(self, texts: List[str], token):
        try:
            return await self._post("/sparse/bm25", {"text": texts}, token=token)
        except Exception as e:
            raise e
        
    async def sparse_tfidf(self, texts: List[str], token):
        try:
            return await self._post("/sparse/tfidf", {"text": texts}, token=token)
        except Exception as e:
            raise e

 