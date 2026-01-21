

ctx = MilvusContext(config)
 
index_manager = IndexManager(ctx)
collection_creator = CollectionCreator(ctx)
crud = CrudOperator(ctx)
search = SearchOperator(ctx, index_manager)

await collection_creator.create_or_verify_collection(index_manager)
ids = await crud.insert(docs)
results = await search.search(dense_vecs, sparse_vec)
