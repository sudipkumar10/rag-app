from app.services.embedding.bge_embedder import bge_embedder
from app.services.indexing.qdrant_client import qdrant_client
from app.core.config import settings
from app.core.logging import logger

class RetrievalPipeline:
    def retrieve(self, query: str, tenant_id: str, top_k: int = 3) -> list[dict]:
        """
        Embed the query, search Qdrant, and return the top_k relevant chunks.
        """
        collection_name = f"{settings.qdrant_collection_prefix}{tenant_id}"
        
        # Check if collection exists (i.e., tenant has uploaded documents)
        if not qdrant_client.client.collection_exists(collection_name):
            return []

        # 1. Embed Query
        query_vector = bge_embedder.embed_texts([query])[0]

        # 2. Search Qdrant
        search_result = qdrant_client.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k
        )
        
        # 3. Format output
        contexts = []
        for hit in search_result.points:
            contexts.append({
                "text": hit.payload.get("text", ""),
                "filename": hit.payload.get("filename", "Unknown"),
                "score": hit.score
            })
            
        logger.info(f"Retrieved {len(contexts)} chunks for query: '{query}'")
        return contexts