from ray import serve
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
import numpy as np
import ray
from Embedding_Service.embeddings.custom_text_vectoriser import EmbeddingGenerator
from typing import List, Dict



@serve.deployment

class TextVectorizer:
    """ A Ray Serve deployment that vectorizes texts(chunks) using an external TEI service."""

    def __init__(self, tei_url, tei_flag, custom_flag, custom_embed_model, micro_batch_size, concurrency):

        """ Initialize the TextVectorizer with TEI service URL."""
        
        self.tei_url = tei_url
        self.tei_flag = tei_flag
        self.custom_flag = custom_flag
        self.model_name = custom_embed_model
        self.micro_batch_size = micro_batch_size
        self.concurrency = concurrency
        
        if self.custom_flag:
            self.generator = EmbeddingGenerator(model_name=self.model_name, micro_batch_size=self.micro_batch_size)
            
        elif self.tei_flag:
            
            self.client = httpx.AsyncClient(
            timeout=30,
            limits=httpx.Limits(
                max_keepalive_connections=200, #  move all hardcoded values to config later
                max_connections=300 
                )
            )


    async def embed(self, payload):
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
                return data

            except Exception as e:
                raise e

        elif self.custom_flag:
            """
            Process texts using Ray Data's map_batches.
            
            This creates parallel workers that each load the model
            and process batches independently.
            """
            try:
            # Create Ray Dataset
                ray_dataset = ray.data.from_items([{"text": text} for text in payload.text])

                # Process using map_batches
                embedded_dataset = ray_dataset.map_batches(
                    self.generator,
                    batch_size=self.micro_batch_size,
                    concurrency=self.concurrency,
                    fn_constructor_kwargs={
                        "model_name": self.model_name,
                        "micro_batch_size": self.micro_batch_size,
                    },
                )
               
                all_embeddings = []
                for batch in embedded_dataset.iter_batches(batch_size=None, batch_format="numpy"):
                    all_embeddings.append(batch["embedding"])
                
                return np.concatenate(all_embeddings, axis=0).tolist() # check will this work
            except Exception as e:
                raise e
        else:
            raise ValueError("No valid embedding method selected. Please enable either TEI or custom embedding.")
                

           


 