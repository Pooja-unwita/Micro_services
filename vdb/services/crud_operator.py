from http.client import HTTPException
from fastapi import HTTPException, status
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
        # res["file_name"] = "file_name" # take file name from metadata if needed
        return res

    async def delete_by_ids(self, collection_name: str, ids: List[int]) -> bool:
        await self.ctx.connect()
        if not ids:
            return True

        expr = f"id in {ids}" if len(ids) > 1 else f"id == {ids[0]}"
        await self.ctx.client.delete(collection_name, filter=expr)
        return True
    
    async def delete_by_json_field(self,collection_name: str, field_name: str,key: str, values:list[str]):
        """
        Delete entities based on a JSON field key-value pair.
        """
        await self.ctx.connect()

        #expr = f'{field_name}["{key}"] == "{value}"'
        expr_parts = [
        f'{field_name}["{key}"] == "{v}"'
        for v in values
    ]
        expr = " or ".join(expr_parts)
        counts={}
        for value in values:
 
            expr = f'{field_name}["{key}"] == "{value}"'
            
            res = await self.ctx.client.query(
                collection_name=collection_name,
                filter=expr,
                output_fields=["count(*)"]
            )
            counts[value] = res[0]["count(*)"] if res else 0
            print(f"{value}: {counts[value]}")
            
        delete_count = await self.ctx.client.delete(
            collection_name=collection_name,
            filter=expr,
        )
        print(counts)
        total_deleted = sum(counts.values())
        response = {
        "files": [
            {"filename": filename, "delete_count": count}
            for filename, count in counts.items()
        ],
        "total_delete_count": total_deleted}
        # if int(delete_count.get("delete_count"))!= sum(total_rows.values()):
        #         raise HTTPException(
        #     status_code=status.HTTP_409_CONFLICT,
        #     detail={
        #         "error": "Delete count mismatch"
        #     }
        # )
        return response
       
        #return True


    async def delete_by_filename(self, collection_name: str, filename:list[str], field_name: str) -> str:
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
        safe_filenames=[file_name.replace('"', '\\"') for file_name in filename]
        total_rows= await self.count_rows_by_field_name(collection_name=collection_name,file_names=safe_filenames,field_name=field_name)
        # safe_filename = filename.replace('"', '\\"')
        expr_parts = [
        f'{field_name} like \'%"filename": "{fn}"%\''
        for fn in safe_filenames
    ]

        expr = " or ".join(expr_parts)

        #expr = f'{field_name} like \'%"filename": "{safe_filename}"%\''
        print("Delete Expression:", expr)
        print("Collection Name:", collection_name)
        delete_count =await self.ctx.client.delete(
            collection_name=collection_name,
            filter=expr,
        )
        print("Delete Count Result:", delete_count)
        response = {
        "files": [
            {"filename": filename, "delete_count": count}
            for filename, count in total_rows.items()
        ],
        "total_delete_count": delete_count.get("delete_count")}
        # if int(delete_count.get("delete_count"))!= sum(total_rows.values()):
        #         raise HTTPException(
        #     status_code=status.HTTP_409_CONFLICT,
        #     detail={
        #         "error": "Delete count mismatch"
        #     }
        # )
        return response
        #return {"filename": filename, "delete_count": delete_count.get("delete_count"), "cost": delete_count.get("cost")}

    async def drop_collection(self, collection_name: str):
            await self.ctx.connect()
            print("Dropping Collection:", collection_name)
            dropped =await self.ctx.client.drop_collection(collection_name)
            print("Drop Collection Result:", dropped)
            return {"collection_name": collection_name, "status": "dropped"}

    async def count_rows_by_field_name(self, collection_name: str, file_names: list[str], field_name: str) -> dict:
        counts = {}
        await self.ctx.connect()
        
        for fn in file_names:
            safe_fn = fn.replace('"', '\\"')
            expr = f'{field_name} like \'%"filename": "{safe_fn}"%\''  
            
            res = await self.ctx.client.query(
                collection_name=collection_name,
                filter=expr,
                output_fields=["count(*)"]
            )
            counts[fn] = res[0]["count(*)"] if res else 0
            print(f"{fn}: {counts[fn]}")
        
        return counts