
from ray import serve
import httpx
import os
from Embedding_Service.models.models import TEIInput
import torch
import gc
from typing import List, Dict
from sentence_transformers import SentenceTransformer

@serve.deployment
class QueryVectorizer:
    """
    A Ray Serve deployment that vectorizes query texts using an external TEI service with configured annotation
    """

    def __init__(self, tei_url, tei_flag, custom_flag, custom_embed_model, query_annotation,device):
        """
        Initialize the QueryVectorizer with TEI service URL and annotation type.
        """
        self.tei_url = tei_url
        self.tei_flag = tei_flag
        self.custom_flag = custom_flag
        self.model_name = custom_embed_model
        self.annotation = query_annotation
        self.device = device


        if self.custom_flag:
            torch.cuda.empty_cache()
            gc.collect()

            self.model = SentenceTransformer(
                self.model_name,
                device=device,
                trust_remote_code=True
            )
            
        elif self.tei_flag:
            
            self.client = httpx.AsyncClient(
            timeout=30,
            limits=httpx.Limits(
                max_keepalive_connections=200, #  move all hardcoded values to config later
                max_connections=300 
                )
            )

    async def embed(self, payload)-> Dict[str, List[List[float]]]:
        """Embed the input texts using the TEI service with specified annotation."""
        if self.tei_flag:

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
                return {"embedding": data["embedding"]} # check the response structure once
            except Exception as e:
                raise
        elif self.custom_flag:
            try:
                text = payload.text

                embedding = self.model.encode(
                    text,
                    convert_to_tensor=False, # check this once
                    show_progress_bar=False
                )

                embedding_list = embedding.tolist()

                return {"embedding": embedding_list}
            except Exception as e:
                raise e
        else:
            raise ValueError("No embedding method specified.")

                    

 