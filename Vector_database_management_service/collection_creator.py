from pymilvus import (
    DataType, FieldSchema, CollectionSchema,
    Function, FunctionType
)
import logging

logger = logging.getLogger(__name__)

class CollectionCreator:
    def __init__(self, ctx):
        self.ctx = ctx

    async def check_schema_match(self,schema_fields, expected_schema)-> bool:
        """
        Compare actual collection fields with expected schema fields.

        Args:
            schema_fields: Fields returned by Milvus describe_collection
            expected_schema: Expected schema dict from configuration

        Returns:
            bool: True if schemas match, False otherwise.

        Raises:
            Exception: Propagates unexpected errors.
        """
        logger.info("Checking schema match between existing collection and expected schema")
        try:
            def dtype_to_str(dtype):
                try:
                    return dtype.name.upper()
                except AttributeError:
                    s = str(dtype).upper()
                    if "DATATYPE." in s:
                        s = s.split("DATATYPE.")[-1]
                    elif "DATATYPE:" in s:
                        s = s.split("DATATYPE:")[-1]
                    return s.split(":")[0].strip(" <>").upper()
            normalized_fields = []
            for f in schema_fields:
                field = {"name": f["name"], "dtype": dtype_to_str(f["type"])}
                if f.get("is_primary") is not None:
                    field["is_primary"] = f["is_primary"]
                if f.get("auto_id") is not None:
                    field["auto_id"] = f["auto_id"]
                if f.get("params"):
                    field.update(f["params"])
                normalized_fields.append(field)
            milvus_dict = {f["name"]: f for f in normalized_fields}
            expected_dict = {f["name"]: f for f in expected_schema}
            for name, exp_field in expected_dict.items():
                act_field = milvus_dict.get(name)
                if not act_field:
                    logger.info(f"Missing field in Milvus: {name}")
                    return False
                for k, v in exp_field.items():
                    if act_field.get(k) != v:
                        logger.info(f"Field '{name}' mismatch in '{k}': expected={v}, got={act_field.get(k)}")
                        return False
            logger.info("Schema matches expected configuration.")
            return True
        except Exception as e:
            logger.error(f"Error while checking schema match: {e}")
            raise

    async def create_schema(self):
        try:
        
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
                description=schema_cfg.get("description", "Milvus collection"),
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
        except Exception as e:
            logger.error(f"Failed to create schema for collection:{e}")
            raise

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

        await index_manager.ensure_search_ready()
        
