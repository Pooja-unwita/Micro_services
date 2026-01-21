from pymilvus import (
    DataType, FieldSchema, CollectionSchema,
    Function, FunctionType
)
import logging

logger = logging.getLogger(__name__)

class CollectionCreator:
    def __init__(self, ctx):
        self.ctx = ctx

    async def check_schema_match(self, schema_fields, expected_schema) -> bool:
        def normalize(dtype):
            try:
                return dtype.name.upper()
            except Exception:
                return str(dtype).split(".")[-1].upper()

        actual = {
            f["name"]: {**f, "dtype": normalize(f["type"])}
            for f in schema_fields
        }
        expected = {f["name"]: f for f in expected_schema}

        for name, exp in expected.items():
            if name not in actual:
                return False
            for k, v in exp.items():
                if actual[name].get(k) != v:
                    return False
        return True

    async def create_schema(self):
        schema_cfg = (
            self.ctx.Hybrid_schema
            if self.ctx.Hybrid_search_flag
            else self.ctx.Schema
        )

        dtype_map = {
            "INT64": DataType.INT64,
            "FLOAT_VECTOR": DataType.FLOAT_VECTOR,
            "VARCHAR": DataType.VARCHAR,
            "SPARSE_FLOAT_VECTOR": DataType.SPARSE_FLOAT_VECTOR,
        }

        fields = []
        for f in schema_cfg["fields"]:
            params = {}
            if f["dtype"] == "FLOAT_VECTOR":
                params["dim"] = f["dim"]
            if f["dtype"] == "VARCHAR":
                params["max_length"] = f["max_length"]
            params.update({k: f[k] for k in ("is_primary", "auto_id") if k in f})

            fields.append(
                FieldSchema(
                    name=f["name"],
                    dtype=dtype_map[f["dtype"]],
                    **params,
                )
            )

        schema = CollectionSchema(
            fields=fields,
            enable_dynamic_field=schema_cfg.get("enable_dynamic_field", True),
        )

        if self.ctx.Hybrid_search_flag:
            fn = Function(
                name=self.ctx.function["name"],
                input_field_names=self.ctx.function["input_field_names"],
                output_field_names=self.ctx.function["output_field_names"],
                function_type=FunctionType.BM25,
            )
            schema.add_function(fn)

        await self.ctx.client.create_collection(
            self.ctx.collection_name, schema=schema
        )

    async def create_or_verify_collection(self, index_manager):
        await self.ctx.connect()

        if self.ctx.sync_client.has_collection(self.ctx.collection_name):
            desc = self.ctx.sync_client.describe_collection(
                self.ctx.collection_name
            )
            schema_cfg = (
                self.ctx.Hybrid_schema
                if self.ctx.Hybrid_search_flag
                else self.ctx.Schema
            )
            if not await self.check_schema_match(
                desc["fields"], schema_cfg["fields"]
            ):
                raise RuntimeError("Schema mismatch")

        else:
            await self.create_schema()

        await index_manager.ensure_indexes()
        await self.ctx.client.load_collection(self.ctx.collection_name)
