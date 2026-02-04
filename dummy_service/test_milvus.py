from handlers.vdb_handler import VDBHandler
from handlers.handler_config_loader import HandlerConfigLoader
from handlers.auth_handler import AuthenticationClient
import asyncio
collection_name = "test_collection"
handler_loader = HandlerConfigLoader()
vdb_config = handler_loader.get_config(config_key="Milvus_Vector_Database")
auth_config = handler_loader.get_config(config_key="Authentication")
semaphore = asyncio.Semaphore(2)
vdb_handler = VDBHandler(config=vdb_config)
auth_client = AuthenticationClient(config=auth_config)
token = None
async def authenticate():
    global token
    if not token:
        token = await auth_client.get_token()
        print("token generated",token,type(token))
    return token

async def test_create_collection():
    await vdb_handler.startup()
    result = await vdb_handler.create_collection(token=await authenticate())
    result2 =await vdb_handler.create_named_collection(collection_name="dear", token=await authenticate())
    print("Create Collection Result:", result)
    print("Create Named Collection Result:", result2) 
    result3 =await vdb_handler.insert_documents(documents=[{ "chunks": "hello world", "vectors": [0.1]*1024, "metadata": '{"filename": "greeting"}' } , 
                                                  { "chunks": "foo bar", "vectors": [0.2]*1024, "metadata": '{"filename": "example"}' } ,
                                                { "chunks": "lorem ipsum", "vectors": [0.3]*1024, "metadata": '{"filename": "lorem", "pgnumber": 1}' }], token=await authenticate())

    print("Insert Documents Result:", result3)
    result4 =await vdb_handler.insert_documents_named_collection(collection_name="dear",documents=[{ "chunks": "hello world", "vectors": [0.1]*1024, "metadata": '{"filename": "greeting"}' } , 
                                                  { "chunks": "foo bar", "vectors": [0.2]*1024, "metadata": '{"filename": "example"}' } ,
                                                { "chunks": "lorem ipsum", "vectors": [0.3]*1024, "metadata": '{"filename": "lorem"}' }], token=await authenticate())
    print("Insert Documents Named Collection Result:", result4)

    await vdb_handler.shutdown()

async def test_drop_collection():
    await vdb_handler.startup()
    result1 = await vdb_handler.drop_collection(token=await authenticate())
    print("Drop Collection Result:", result1)
    result2 = await vdb_handler.drop_named_collection(collection_name="dear", token=await authenticate())
    print("Drop Named Collection Result:", result2)
    await vdb_handler.shutdown()


async def test_delete_by_filename():
    await vdb_handler.startup()
    result = await vdb_handler.delete_documents_by_filename(filename= "lorem",field_name="metadata", token=await authenticate())
    print("Delete Documents by Filename Result:", result)
    await vdb_handler.shutdown()

async def test_search():
    await vdb_handler.startup()
    result = await vdb_handler.search(dense_vecs=[[0.1]*1024, [0.2]*1024], token=await authenticate())
    print("Search Result:", result)
    result_named = await vdb_handler.search_named_collection(collection_name="dear",dense_vecs=[[0.1]*1024, [0.2]*1024], token=await authenticate())
    print("Search Named Collection Result:", result_named)
    await vdb_handler.shutdown()

async def test_parallel_operations():
    await vdb_handler.startup()

    insert_task = vdb_handler.insert_documents(
        documents=[
            {
                "chunks": "parallel hello",
                "vectors": [0.4] * 1024,
                "metadata": '{"filename": "parallel_1"}'
            },
            {
                "chunks": "parallel world",
                "vectors": [0.5] * 1024,
                "metadata": '{"filename": "parallel_2"}'
            }
        ],token=await authenticate()
    )

    delete_task = vdb_handler.delete_documents_by_filename(
        filename="parallel_1",
        field_name="metadata",token=await authenticate()
    )

    search_task = vdb_handler.search(
        dense_vecs=[[0.1] * 1024],token=await authenticate()
    )

    results = await asyncio.gather(
        insert_task,
        delete_task,
        search_task,
        return_exceptions=True
    )

    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"Task {i} failed:", result)
        else:
            print(f"Task {i} result:", result)

    await vdb_handler.shutdown()


async def simulate_user(user_id: int):
    async with semaphore:
        token = await authenticate()

        # insert_task = asyncio.create_task(
        #     vdb_handler.insert_documents(
        #         documents=[
        #             {
        #                 "chunks": f"hello from user {user_id}",
        #                 "vectors": [0.4] * 1024,
        #                 "metadata": f'{{"filename": "parallel_2"}}'
        #             }
        #         ],
        #         token=token
        #     )
        # )

        delete_task = asyncio.create_task(
            vdb_handler.delete_documents_by_filename(
                filename="example",
                field_name="metadata",
                token=token
            )
        )

        # search_task = asyncio.create_task(
        #     vdb_handler.search(
        #         dense_vecs=[[0.1] * 1024],
        #         token=token
        #     )
        # )

        results = await asyncio.gather(
            # insert_task,
            delete_task,
            # search_task,
            return_exceptions=True
        )

        return {
            "user_id": user_id,
            "results": results
        }
async def test_concurrent_users(user_count: int = 20):
    await vdb_handler.startup()

    user_tasks = [
        asyncio.create_task(simulate_user(user_id=i))
        for i in range(user_count)
    ]

    all_results = await asyncio.gather(
        *user_tasks,
        return_exceptions=True
    )

    for result in all_results:
        if isinstance(result, Exception):
            print("User failed:", result)
        else:
            print(result)
            print(f"User {result['user_id']} completed")

    await vdb_handler.shutdown()

 

if __name__ == "__main__":    
    import asyncio

    #asyncio.run(test_concurrent_users(user_count=2))
    #asyncio.run(test_drop_collection())
    asyncio.run(test_parallel_operations())
    #asyncio.run(test_create_collection())
    #asyncio.run(test_delete_by_filename())
