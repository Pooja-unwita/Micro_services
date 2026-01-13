import asyncio
import logging
from typing import List, Optional
import httpx
from auth_handler import AuthenticationClient 

class EmbeddingClient:
    """
    High-performance async HTTP client for communicating with the Embedding Service.
    Intended to be reused inside Ray Serve deployments.
    """

    def __init__(
        self,
        caller:str ,
        service_name: str = "embedding_service",
        #secret_key: str = "secret_keyy",
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
        self.caller=caller
        self.base_url = base_url
        self.auth_client=AuthenticationClient(service_name=service_name)
        self.service_name = service_name
        #self.secret_key = secret_key
        self.client: Optional[httpx.AsyncClient] = None
        self._headers = {"Content-Type": "application/json"}
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self._token_lock = asyncio.Lock() # To prevent multiple simultaneous token refreshes


    async def startup(self):
        """Initialize shared client and fetch initial token."""
        if self.client is None:
            await self.auth_client.get_token(caller=self.caller) # use AuthenticationClient to get token
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=None,
                limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
            )
            self.client.headers.update(self._headers)

    async def shutdown(self):
        """Close the connection pool gracefully."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _post(self, path: str, payload: dict):
        """Send POST request and handle token refresh on 401."""
        if not self.client:
            await self.startup()

        async with self.semaphore:
            try:
                response = await self.client.post(path, json=payload)
                response.raise_for_status()
                token=  response.json()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logging.warning("Auth token expired, refreshing token...")

                    # Only one coroutine refreshes the token at a time
                    async with self._token_lock:
                        await self.get_token()
                        self.client.headers.update(self._headers)

                    # Retry the request once
                    response = await self.client.post(path, json=payload)
                    response.raise_for_status()
                    return response.json()

                raise RuntimeError(
                    f"HTTP {e.response.status_code} from {path}: {e.response.text}"
                ) from e

            except httpx.RequestError as e:
                raise RuntimeError(
                    f"Error contacting {self.base_url}{path}: {e}"
                ) from e

    async def dense_text(self, texts: List[str]):
        return await self._post("/dense/text", {"text": texts})

    async def dense_query(self, texts: List[str]):
        return await self._post("/dense/query", {"text": texts})

    async def sparse_splade(self, texts: List[str]):
        return await self._post("/sparse/splade", {"text": texts})

    async def sparse_bm25(self, texts: List[str]):
        return await self._post("/sparse/bm25", {"text": texts})

    async def sparse_tfidf(self, texts: List[str]):
        return await self._post("/sparse/tfidf", {"text": texts})

 