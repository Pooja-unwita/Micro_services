from pymilvus import AnnSearchRequest, RRFRanker
import logging

logger = logging.getLogger(__name__)

class SearchOperator:
    def __init__(self, ctx, index_manager):
        self.ctx = ctx
        self.index_manager = index_manager

    async def dense_search(self, vectors, top_k=None, filter_expr=None):
        await self.ctx.connect()
        top_k = top_k or self.ctx.top_k

        index_map = await self.index_manager.has_index()
        index_type = index_map[self.ctx.ann_field]

        cfg = next(
            c for c in self.ctx.dense_index_list
            if c["index_type"] == index_type
        )

        return await self.ctx.client.search(
            collection_name=self.ctx.collection_name,
            data=vectors,
            anns_field=self.ctx.ann_field,
            search_params=cfg["search_params"],
            limit=top_k,
            output_fields=self.ctx.output_fields,
            filter=filter_expr,
        )

    async def hybrid_search(self, dense_vecs, sparse_vec, top_k=None):
        await self.ctx.connect()
        top_k = top_k or self.ctx.top_k

        index_map = await self.index_manager.has_index()
        reqs = []

        for field in self.ctx.Hybrid_search["annn_fields"]:
            idx_type = index_map[field]
            cfg = next(
                c for c in self.ctx.index_config_list
                if c["index_type"] == idx_type
            )

            data = sparse_vec if "SPARSE" in idx_type else dense_vecs
            reqs.append(
                AnnSearchRequest(
                    data=data,
                    anns_field=field,
                    param=cfg["search_params"],
                    limit=top_k,
                )
            )

        return await self.ctx.client.hybrid_search(
            collection_name=self.ctx.collection_name,
            reqs=reqs,
            ranker=RRFRanker(60),
            output_fields=self.ctx.output_fields,
        )

    async def search(self, dense_vecs, sparse_vec=None, **kwargs):
        if self.ctx.Hybrid_search_flag:
            return await self.hybrid_search(dense_vecs, sparse_vec, **kwargs)
        return await self.dense_search(dense_vecs, **kwargs)
