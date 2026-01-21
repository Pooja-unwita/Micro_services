import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CrudOperator:
    def __init__(self, ctx):
        self.ctx = ctx

    async def insert(self, documents: List[Dict[str, Any]]) -> List[int]:
        await self.ctx.connect()
        if not documents:
            return []

        res = await self.ctx.client.insert(
            self.ctx.collection_name, documents
        )
        return res.get("ids", [])

    async def delete_by_ids(self, ids: List[int]) -> bool:
        await self.ctx.connect()
        if not ids:
            return True

        expr = f"id in {ids}" if len(ids) > 1 else f"id == {ids[0]}"
        await self.ctx.client.delete(self.ctx.collection_name, filter=expr)
        return True

    async def drop_collection(self):
        await self.ctx.connect()
        await self.ctx.client.drop_collection(self.ctx.collection_name)

    async def list_collections(self) -> list:
        await self.ctx.connect()
        return await self.ctx.client.list_collections()
