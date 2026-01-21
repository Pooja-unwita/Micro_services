from fastapi import APIRouter, Request
from typing import Optional, Dict, Any

router = APIRouter()

@router.post("/")
async def search(
    dense_vectors: list,
    sparse_vector: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
    request: Request = None
):
    search_op = request.app.state.search
    results = await search_op.search(
        dense_vecs=dense_vectors,
        sparse_vec=sparse_vector,
        top_k=top_k
    )
    return {"results": results}
