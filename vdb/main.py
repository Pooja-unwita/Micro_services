from vdb.routers.milvus_service import MilvusService

def milvus_service_builder(args: dict):
    return MilvusService.bind(milvus_config= args["milvus_config"])