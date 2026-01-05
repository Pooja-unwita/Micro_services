from ray import serve
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os


@serve.deployment
class TextVectorizer:
    def __init__(self, tei_url):
        self.tei_url = tei_url
        self.client = httpx.AsyncClient(
            timeout=30,
            limits=httpx.Limits(
                max_keepalive_connections=200, #  move all hardcoded values to config later
                max_connections=300 
            )
        )

        self.replica_id = os.getpid() #remove later if not needed

    async def embed(self, payload):
        try:
    
            resp = await self.client.post(
                self.tei_url,
                json={"inputs": payload.text}, # change this as per qery vectorizer
                timeout = 30
            )
            resp.raise_for_status()
            data = resp.json()
            return data

        except Exception as e:
            raise
            


