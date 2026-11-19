from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
from app.core.logging import logger

# BGE-M3 outputs 1024-dimensional vectors
VECTOR_SIZE = 1024 

class QdrantStorageClient:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )

    def ensure_collection(self, collection_name: str):
        """Creates the collection if it doesn't exist."""
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {collection_name}")

    def upsert_chunks(self, collection_name: str, points: list[PointStruct]):
        """Insert chunks and their vectors into Qdrant."""
        if not points:
            return
            
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} points to Qdrant collection: {collection_name}")

qdrant_client = QdrantStorageClient()