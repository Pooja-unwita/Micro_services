from pydantic import BaseModel
from typing import List, Literal



class Token(BaseModel):
    '''
    Docstring for Token
    '''
    access_token: str
    token_type: str

class JWK(BaseModel):
    '''
    Docstring for JWK
    '''
    kty: Literal["RSA"]
    kid: str
    use: Literal["sig"]
    alg: Literal["RS256"]
    n: str
    e: str

class JWKS(BaseModel):
    '''
    Docstring for JWKS
    '''
    keys: List[JWK]
