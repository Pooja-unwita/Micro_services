from pydantic import BaseModel
from pydantic import Field
from typing import List,Dict,Any

class SearchInput(BaseModel):
    dense_vector: list[list[float]]
    sparse_vector: list[dict] | None = None
    top_k: int | None = None
    filter_expr: str | None = None

class SearchNamedCollectionInput(BaseModel):
    # collection_name: str
    dense_vector: List[List[float]]
    sparse_vector: List[Dict[str, float]] | None = None
    top_k: int | None = None
    filter_expr: str | None = None

class CollectionNameInput(BaseModel):
    collection_name: str

class CreateCollectionResponse(BaseModel):
    collection_name: str
    status: str

class DropCollectionInput(BaseModel):
    collection_name: str

class DropcollectionResponse(BaseModel):
    collection_name: str
    drop_status: bool

class DeleteByFilenameInput(BaseModel):
    filenames:List[str]

class DeleteByFilenameResponse(BaseModel):
    filename: str
    delete_count: int 
    cost: float

class InsertResponse(BaseModel):
    insert_count: int
    ids: list[int]
    
class ChunkResult(BaseModel):
    id: int
    distance: float
    filename: str
    chunks: str

class SearchResponse(BaseModel):
    collection_name : str
    chunks: List[List[ChunkResult]]

class DocumentInput(BaseModel):
    chunks: str 
    vectors: List[float] 
    metadata: Dict[str, Any] 
     
class InsertDocumentsRequest(BaseModel):
    documents: List[DocumentInput]


class FileDeleteInfo(BaseModel):
    filename: str
    delete_count: int

class BulkDeleteResponse(BaseModel):
    collection_name:str
    files: List[FileDeleteInfo]
    total_delete_count: int

