from pydantic import BaseModel
from typing import List, Dict


class EmbedInput(BaseModel):
    text: list[str] 

class TEIInput(BaseModel):
    inputs: list[str]

class Token(BaseModel):
    access_token: str
    token_type: str

class DenseEmbeddingResponse(BaseModel):
    embedding: List[List[float]]

class SparseEmbeddingResponse(BaseModel):
    embedding: List[Dict[int, float]]