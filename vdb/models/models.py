from pydantic import BaseModel

class SearchInput(BaseModel):
    dense_vector: list[list[float]]
    sparse_vector: list[dict] | None = None
    top_k: int | None = None
    filter_expr: str | None = None

class SearchNamedCollectionInput(BaseModel):
    collection_name: str
    dense_vector: list[list[float]]
    sparse_vector: list[dict] | None = None
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
    status: str

class DeleteByFilenameInput(BaseModel):
    filename: str
    field_name: str = "metadata"

class DeleteByFilenameResponse(BaseModel):
    filename: str
    deleted_count: int
    cost: float

class InsertResponse(BaseModel):
    insert_count: int
    ids: list[int]
    file_name: str



