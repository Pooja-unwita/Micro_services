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

class DeleteByFilenameInput(BaseModel):
    filename: str
    field_name: str = "metadata"