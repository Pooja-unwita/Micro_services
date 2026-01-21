from ray import serve
from fastapi import FastAPI
import logging

from Vector_database_management_service.context import MilvusContext
from vdb.services.collection_creator import CollectionCreator
from Vector_database_management_service.index_manager import IndexManager
from Vector_database_management_service.crud_operator import CrudOperator
from Vector_database_management_service.search_operator import SearchOperator

from Vector_database_management_service.routers.health import router as health_router
from Vector_database_management_service.routers.collections import router as collections_router
from Vector_database_management_service.routers.documents import router as documents_router
from Vector_database_management_service.routers.search import router as search_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Milvus Vector Service")


@serve.deployment
@serve.ingress(app)
class MilvusService:
    def __init__(self, milvus_config: dict):
        """
        Runs ONCE per Ray Serve replica
        """
        self.ctx = MilvusContext(milvus_config)

        self.index_manager = IndexManager(self.ctx)
        self.collection_creator = CollectionCreator(self.ctx)
        self.crud = CrudOperator(self.ctx)
        self.search = SearchOperator(self.ctx, self.index_manager)

        # inject shared state into routers
        app.state.ctx = self.ctx
        app.state.collection_creator = self.collection_creator
        app.state.index_manager = self.index_manager
        app.state.crud = self.crud
        app.state.search = self.search

        app.include_router(health_router)
        app.include_router(collections_router, prefix="/collections")
        app.include_router(documents_router, prefix="/documents")
        app.include_router(search_router, prefix="/search")

    @app.on_event("startup")
    async def startup(self):
        """
        Called once per replica
        """
        await self.ctx.connect()
        logger.info("MilvusService replica started")

    @app.on_event("shutdown")
    async def shutdown(self):
        if self.ctx.client:
            await self.ctx.client.close()
        if self.ctx.sync_client:
            self.ctx.sync_client.close()
        logger.info("MilvusService replica shutdown")
