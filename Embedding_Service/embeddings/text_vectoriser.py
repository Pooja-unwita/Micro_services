import gc
from ray import serve
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
import numpy as np
import ray
import torch
from Embedding_Service.models.models import EmbedInput
import gc
from sentence_transformers import SentenceTransformer

from typing import List, Dict



@serve.deployment

class TextVectorizer:
    """ A Ray Serve deployment that vectorizes texts(chunks) using an external TEI service."""

    def __init__(self, tei_url, tei_flag, custom_flag, custom_embed_model, concurrency, device):

        """ Initialize the TextVectorizer with TEI service URL."""
        
        self.tei_url = tei_url
        self.tei_flag = tei_flag
        self.custom_flag = custom_flag
        self.model_name = custom_embed_model
        self.concurrency = concurrency
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

    async def embed(self, payload: EmbedInput) -> Dict[str, List[List[float]]]:
        """Embed the input texts (chunks) using the TEI service."""

        if self.tei_flag:

            try:
        
                resp = await self.client.post(
                    self.tei_url,
                    json={"inputs": payload.text}, # change this as per query vectorizer
                    timeout = 30
                )
                resp.raise_for_status()
                data = resp.json()
                return {"embedding": data["embedding"]} # check the response structure once

            except Exception as e:
                raise e

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
 