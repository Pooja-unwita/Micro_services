import logging

logger = logging.getLogger(__name__)

class IndexManager:
    def __init__(self, ctx):
        self.ctx = ctx

    async def has_index(self) -> dict | None:
        await self.ctx.connect()
        indexes = await self.ctx.client.list_indexes(self.ctx.collection_name)
        if not indexes:
            return None

        result = {}
        for idx in indexes:
            desc = await self.ctx.client.describe_index(
                self.ctx.collection_name, idx
            )
            result[idx] = desc["index_type"]
        return result

    async def parameters_match(self, field_name: str) -> bool:
        desc = await self.ctx.client.describe_index(
            self.ctx.collection_name, field_name
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

    async def ensure_indexes(self):
        await self.ctx.connect()
        existing = await self.has_index() or {}

        schema = (
            self.ctx.Hybrid_schema
            if self.ctx.Hybrid_search_flag
            else self.ctx.Schema
        )

        params = self.ctx.client.prepare_index_params()

        for field in schema["fields"]:
            name = field["name"]
            dtype = field["dtype"]

            if name in existing and await self.parameters_match(name):
                continue

            if name in existing:
                await self.ctx.client.drop_index(
                    self.ctx.collection_name, name
                )

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
                self.ctx.collection_name, params
            )
