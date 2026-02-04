from pymilvus import AsyncMilvusClient, MilvusClient
from vdb.utils.set_attribute import AttributeSetter
import copy
import logging

logger = logging.getLogger(__name__)

class MilvusContext:
    def __init__(self, milvus_configs: dict):
        AttributeSetter.set_attributes(self, milvus_configs)
        AttributeSetter.set_attributes(self, self.Hybrid_search)

        self.client: AsyncMilvusClient | None = None
        self.sync_client: MilvusClient | None = None

        self.dense_index_list = self.indexes.get("Dense_index", [])
        self.sparse_index_list = self.indexes.get("Sparse_index", [])
        self.index_config_list = [
            cfg for configs in self.indexes.values() for cfg in configs
        ]

    async def connect(self):
        if not self.client:
            self.client = AsyncMilvusClient(
                uri=f"http://{self.host}:{self.port}"
            )
            self.sync_client = MilvusClient(
                uri=f"http://{self.host}:{self.port}"
            )
            logger.info("Connected to Milvus")
     
            

    def with_collection(self, collection_name: str):
        new_ctx = copy.copy(self)
        new_ctx.collection_name = collection_name
        return new_ctx
