from pydantic import BaseModel, conlist
from typing import List, Dict

Vector = conlist(float, min_length=1024, max_length=1024)

class EmbedInput(BaseModel):
    text: list[str] 

class TEIInput(BaseModel):
    inputs: list[str]

class Token(BaseModel):
    access_token: str
    token_type: str

class DenseEmbeddingResponse(BaseModel):
    #embedding: List[List[float]]
    embedding: List[Vector]

class SparseEmbeddingResponse(BaseModel):
    embedding: List[Dict[int, float]]