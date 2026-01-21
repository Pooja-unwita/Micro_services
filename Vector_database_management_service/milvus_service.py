
from ray import serve
from Vector_database_management_service.serve_app import MilvusService

def milvus_service_builder(args: dict[str, dict]):
    """
    Docstring for milvus_service_builder
    :param args: Description
    :type args: dict[str, dict]
    """
    milvus_service = MilvusService.bind(args["milvus_config"])

    return milvus_service
