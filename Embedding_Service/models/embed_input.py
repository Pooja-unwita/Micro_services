from pydantic import BaseModel

class EmbedInput(BaseModel):
    text: list[str] 

class TEIInput(BaseModel):
    inputs: list[str]

class Token(BaseModel):
    access_token: str
    token_type: str