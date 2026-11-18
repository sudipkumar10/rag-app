from qdrant_client.models import PointStruct
from app.services.chunking.schemas import Chunk
from app.services.embedding.bge_embedder import bge_embedder
from app.services.indexing.qdrant_client import qdrant_client
from app.core.logging import logger
from app.core.config import settings 

class IndexingPipeline:
    def process(self, chunks: list[Chunk], tenant_id: str):
        if not chunks:
            return

        logger.info(f"Starting indexing for {len(chunks)} chunks (Tenant: {tenant_id})")
        
        # 1. Extract texts for embedding
        texts = [chunk.text for chunk in chunks]
        
        # 2. Generate Embeddings (Batch)
        vectors = bge_embedder.embed_texts(texts)
        
        # 3. Format for Qdrant
        collection_name = f"{settings.qdrant_collection_prefix}{tenant_id}"
        qdrant_client.ensure_collection(collection_name)
        
        points = []
        for chunk, vector in zip(chunks, vectors):
            points.append(
                PointStruct(
                    id=str(chunk.chunk_id),
                    vector=vector,
                    payload={
                        "document_id": str(chunk.metadata.document_id),
                        "tenant_id": tenant_id,
                        "filename": chunk.metadata.original_filename,
                        "text": chunk.text,
                        "chunk_index": chunk.metadata.chunk_index,
                        "total_chunks": chunk.metadata.total_chunks,
                        "token_count": chunk.metadata.token_count
                    }
                )
            )
            
        # 4. Upsert to Qdrant in batches of 100 to avoid timeouts
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            qdrant_client.upsert_chunks(collection_name, batch)
            
        logger.info(f"Successfully indexed {len(points)} chunks.")