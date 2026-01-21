from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/")
async def create_collection(request: Request):
    creator = request.app.state.collection_creator
    index_manager = request.app.state.index_manager

    await creator.create_or_verify_collection(index_manager)
    return {"status": "collection ready"}


@router.get("/")
async def list_collections(request: Request):
    crud = request.app.state.crud
    collections = await crud.list_collections()
    return {"collections": collections}


@router.delete("/{collection_name}")
async def drop_collection(collection_name: str, request: Request):
    ctx = request.app.state.ctx
    ctx.collection_name = collection_name

    await request.app.state.crud.drop_collection()
    return {"status": "dropped"}
