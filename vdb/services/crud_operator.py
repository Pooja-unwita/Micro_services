from http.client import HTTPException
import logging
from typing import List, Dict, Any, Union


logger = logging.getLogger(__name__)

class CrudOperator:
    def __init__(self, ctx):
        self.ctx = ctx

    async def insert(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[int]:
        await self.ctx.connect()
        if not documents:
            return []

        res = await self.ctx.client.insert(
            collection_name=collection_name, data=documents
        )
        res["file_name"] = "file_name" # take file name from metadata if needed
        return res

    async def delete_by_ids(self, collection_name: str, ids: List[int]) -> bool:
        await self.ctx.connect()
        if not ids:
            return True

        expr = f"id in {ids}" if len(ids) > 1 else f"id == {ids[0]}"
        await self.ctx.client.delete(collection_name, filter=expr)
        return True
    
    async def delete_by_json_field(self,collection_name: str, field_name: str,key: str,value: str) -> bool:
        """
        Delete entities based on a JSON field key-value pair.
        """
        await self.ctx.connect()

        expr = f'{field_name}["{key}"] == "{value}"'

        await self.ctx.client.delete(
            collection_name=collection_name,
            filter=expr,
        )
        return True


    async def delete_by_filename(self, collection_name: str, filename: str, field_name: str) -> str:
        """
        Delete entities where a VARCHAR field contains a given filename.

        Example stored value:
            {"filename":"a.pdf","author":"andrew"}

        Generated filter:
            metadata like "%\"filename\":\"a.pdf\"%"
        """
        await self.ctx.connect()

        if not field_name or not filename:
            raise ValueError("Both field_name and filename must be provided.")

        # Escape quotes defensively
        safe_filename = filename.replace('"', '\\"')

        expr = f'{field_name} like \'%"filename": "{safe_filename}"%\''
        print("Delete Expression:", expr)
        print("Collection Name:", collection_name)
        delete_count =await self.ctx.client.delete(
            collection_name=collection_name,
            filter=expr,
        )
        print("Delete Count Result:", delete_count)
        return {"filename": filename, "delete_count": delete_count.get("delete_count"), "cost": delete_count.get("cost")}

    async def drop_collection(self, collection_name: str):
            await self.ctx.connect()
            print("Dropping Collection:", collection_name)
            dropped =await self.ctx.client.drop_collection(collection_name)
            print("Drop Collection Result:", dropped)
            #return dropped
            return {"collection_name": collection_name, "status": "dropped"}

