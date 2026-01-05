from sklearn.feature_extraction.text import TfidfVectorizer
from pymilvus.model.sparse.bm25.tokenizers import build_default_analyzer
from pymilvus.model.sparse import BM25EmbeddingFunction
from pymilvus import model 
import asyncio
import ray
from ray import serve
from typing import List, Dict

@serve.deployment
class SparseVectorizer:
    def __init__(self, splade_model_name, splade_device, tfidf_max_features):
        try:
            analyzer = build_default_analyzer()
            self.splade_model_name= splade_model_name
            self.splade_device = splade_device
            self.bm25_ef = BM25EmbeddingFunction(analyzer)
            self.splade_ef = model.sparse.SpladeEmbeddingFunction(model_name=self.splade_model_name, device = self.splade_device)
            self.tf_vectorizer = TfidfVectorizer(max_features= tfidf_max_features)
            
        except Exception as e:
            #logger.error(f"Error initializing Sparse Vectorizer: {e}")
            raise 


    def csr_to_dict(self, csr_vec) -> list[dict]:
        """
        Convert a list of csr_matrix rows into list of {index: value} dicts.
        Args:
            csr_vec: List of csr_matrix rows.
        Returns:
            List[Dict[int, float]]: List of dictionaries representing sparse vectors.
        """
        try:
            dicts = []
            for row in csr_vec:
                indices = row.indices
                values = row.data
                dicts.append({int(i): float(v) for i, v in zip(indices, values)})
            return dicts
        except Exception as e:
            #logger.error(f"Error converting CSR to dict: {e}")
            raise
    
    async def bm25_vectorise_text(self, docs:list) -> List[dict]:
        """
        Generate sparse embeddings for a list of texts using BM25.

        Args:
            docs (List[str]): List of texts to embed.
        Returns:
            List[Dict[int, float]]: List of BM25 sparse embeddings.
        Raises:
            Exception: If embedding fails.
        """
        try: 
            
            self.bm25_ef.fit(docs.text)
            docs_embeddings_org = self.bm25_ef.encode_documents(docs.text)
            docs_embeddings = self.csr_to_dict(docs_embeddings_org)
            #logger.info("Embedding produced for BM25 vectoriser")
            return docs_embeddings
        except Exception as e:
            #logger.error(f"Error during BM25 text vectorization: {e}")
            raise

    async def build_splade_embeddings(self, docs: list) -> list[Dict]:
        """
        Generate sparse embeddings for a list of texts using SPLADE and add them to their metadata.
        Returns:
            List[Dict[int, float]]: List of SPLADE sparse embeddings.
        Raises:
            Exception: If embedding fails.
        """
        
        try:

            docs_embeddings = self.splade_ef.encode_documents(docs.text)
            docs_embeddings_conv= self.csr_to_dict(docs_embeddings)
            #logger.info("Embedding produced for Splade vectoriser")
            return docs_embeddings_conv
        except Exception as e:
            #logger.error(f"Error during SPLADE text vectorization: {e}")
            raise

    async def build_TFIDF_embeddings(self, docs: list) -> list[Dict]:
        """
        Generate sparse embeddings for a list of text using TF-IDF and add them to their metadata.
        Args:
            documents (list[Document]): List of documents to embed.
        Returns:
            List[Dict[int, float]]: List of TF-IDF sparse embeddings.
        Raises:
            Exception: If embedding fails.
        """
        try:
            vectors_sparse = await asyncio.to_thread(self.tf_vectorizer.fit_transform, docs.text)
        
        # Convert CSR matrix to list of dicts (same as other methods)
            docs_embeddings = self.csr_to_dict(vectors_sparse)
            #logger.info("Embedding produced for TFIDF vectoriser")
            return docs_embeddings
        
        except Exception as e:
            #logger.error(f"Error during TF-IDF text vectorization: {e}")
            raise
        
   