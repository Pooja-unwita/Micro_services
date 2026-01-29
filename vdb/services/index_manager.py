import logging

logger = logging.getLogger(__name__)

class IndexManager:
    def __init__(self, ctx):
        self.ctx = ctx

    async def index_list(self, collection_name:str) -> dict | None:
        await self.ctx.connect()
        indexes = await self.ctx.client.list_indexes(collection_name)
        if not indexes:
            return None

        result = {}
        for idx in indexes:
            desc = await self.ctx.client.describe_index(
                collection_name, idx
            )
            result[idx] = desc["index_type"]
        return result

    async def parameters_match(self, field_name: str, collection_name: str) -> bool:
        desc = await self.ctx.client.describe_index(
            collection_name, field_name
        )
        for cfg in self.ctx.index_config_list:
            if cfg["index_type"] == desc["index_type"]:
                if cfg["search_params"]["metric_type"] != desc["metric_type"]:
                    return False
                return all(
                    str(desc.get(k)) == str(v)
                    for k, v in cfg["index_params"].items()
                )
        return False

    async def ensure_indexes(self, collection_name: str) -> None:
        await self.ctx.connect()
        existing = await self.index_list(collection_name) or {}

        schema = (
            self.ctx.Hybrid_schema
            if self.ctx.Hybrid_search_flag
            else self.ctx.Schema
        )

        params = self.ctx.client.prepare_index_params()

        for field in schema["fields"]:
            name = field["name"]
            dtype = field["dtype"]

            if name in existing and await self.parameters_match(name, collection_name):
                continue

            if name in existing:
                await self.drop_index(name)

            if dtype == "FLOAT_VECTOR":
                cfg = self.ctx.dense_index_list[0]
                params.add_index(
                    field_name=name,
                    index_type=cfg["index_type"],
                    metric_type=cfg["search_params"]["metric_type"],
                    params=cfg["index_params"],
                )

            if dtype == "SPARSE_FLOAT_VECTOR" and self.ctx.Hybrid_search_flag:
                cfg = self.ctx.sparse_index_list[0]
                params.add_index(
                    field_name=name,
                    index_type=cfg["index_type"],
                    metric_type=cfg["search_params"]["metric_type"],
                    params=cfg["index_params"],
                )

        if params:
            await self.ctx.client.create_index(
                collection_name, params
            )

    async def drop_index(self,field_name: str, collection_name: str)->None:
        """Drop index asynchronously"""
        try:
            if not self.ctx.client:
                await self.ctx.connect()
            await self.release(collection_name=collection_name)
            await self.ctx.client.drop_index(collection_name, field_name)
            logger.info(f"Index on '{field_name}' dropped.")
        except Exception as e:
            raise RuntimeError(f"Failed to drop index: {e}")


    async def is_loaded(self, collection_name: str)-> str:
        """Check if collection is loaded into memory asynchronously"""
        try:
            if not self.ctx.client:
                await self.ctx.connect()
            loaded = await self.ctx.client.get_load_state(collection_name)
            
            state = loaded["state"].name
        
            if state == "Loaded":
                return True

                logger.info(f"Collection '{collection_name}' is loaded in memory.")
            else:
                return False
            logger.info(f"Collection '{collection_name}' loaded status: {loaded}")
            return loaded
        
        # except Exception as e:
        #     raise e
        #     loaded = await self.ctx.client.get_load_state(collection_name)
        #     logger.info(f"Collection '{collection_name}' loaded status: {loaded}")
        #     return loaded
        except Exception as e:
            logger.error(f"Failed to check if collection is loaded: {e}")
            raise RuntimeError(f"Failed to check if collection is loaded: {e}")

    async def ensure_search_ready(self, collection_name: str):
        await self.ensure_indexes(collection_name)
        
        if not await self.is_loaded(collection_name):
           
            await self.load(collection_name)

    async def load(self, collection_name: str) -> bool:
        """Load collection into memory asynchronously"""
        try:
            if not self.ctx.client:
                await self.ctx.connect()
        except Exception as e:
            raise e
        try:
            await self.ctx.client.load_collection(collection_name)
           
            logger.info(f"Collection '{collection_name}' loaded.")
            return True
        except Exception as e:
            logger.error(f"Failed to load collection: {e}")
            raise RuntimeError(f"Failed to load collection: {e}")

    async def release(self, collection_name: str)-> None:
        """Release collection from memory asynchronously"""
        try:
            if not self.ctx.client:
                await self.ctx.connect()

            await self.ctx.client.release_collection(collection_name)
            logger.info(f"Collection '{collection_name}' released from memory.")
        except Exception as e:
            raise RuntimeError(f"Failed to release collection: {e}")