
from ray import serve
import httpx
import os
from Embedding_Service.models.models import TEIInput

@serve.deployment
class QueryVectorizer:
    """
    A Ray Serve deployment that vectorizes query texts using an external TEI service with configured annotation
    """

    def __init__(self, tei_url, query_annotation):
        """
        Initialize the QueryVectorizer with TEI service URL and annotation type.
        """
        self.tei_url = tei_url
        self.annotation = query_annotation
        self.client = httpx.AsyncClient(
            timeout=30,
            limits=httpx.Limits(
                max_keepalive_connections=200,
                max_connections=300
            )
        )
        #self.replica_id = os.getpid() #remove later if not needed

    async def embed(self, payload):
        """Embed the input texts using the TEI service with specified annotation."""
        try:
            headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"}

            annotated_query = [f"{self.annotation}:{i}" for i in payload.text]
            req = TEIInput(inputs=annotated_query)
            resp = await self.client.post(
                self.tei_url,
                json=req.model_dump(),headers=headers,
                #json={"inputs": annotated_query}, # check if this is needed
                timeout = 30
            )
            resp.raise_for_status()
            data = resp.json()
            return data
        except Exception as e:
            raise
            

