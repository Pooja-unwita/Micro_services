from fastapi import APIRouter, Request
from typing import List, Dict, Any

router = APIRouter()

@router.post("/")
async def insert_documents(
    documents: List[Dict[str, Any]],
    request: Request
):
    crud = request.app.state.crud
    ids = await crud.insert(documents)
    return {"ids": ids}


@router.delete("/")
async def delete_documents(ids: List[int], request: Request):
    crud = request.app.state.crud
    await crud.delete_by_ids(ids)
    return {"status": "deleted"}
