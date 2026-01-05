from ray import serve
import ray
from Embedding_Service.embeddings.query_vectoriser import QueryVectorizer
from Embedding_Service.embeddings.text_vectoriser import TextVectorizer
from Embedding_Service.embeddings.sparse_vectoriser import SparseVectorizer
from Embedding_Service.routers.routers import EmbeddingService

def app_builder(args: dict[str, str]):



    query = QueryVectorizer.bind(
        args["tei_url"],
        args["query_annotation"]
    )

    text = TextVectorizer.bind(
        args["tei_url"]
    )

    sparse = SparseVectorizer.bind(
        splade_model_name = args["splade_model_name"],
        tfidf_max_features =args["tfidf_max_features"],
        splade_device = args["splade_device"]
    )

    embedd_app = EmbeddingService.bind(
        query,
        text,
        sparse,
    )

    return embedd_app
