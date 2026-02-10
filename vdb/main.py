from vdb.routers.milvus_service import MilvusService
from ray.serve.handle import DeploymentHandle

def milvus_service_builder(args: dict)->DeploymentHandle:
    return MilvusService.bind(milvus_config= args["milvus_config"])