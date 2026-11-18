from sentence_transformers import SentenceTransformer
from app.services.embedding.base import BaseEmbedder
from app.core.logging import logger

class BGEEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully.")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
            
        # Batch processing ensures memory doesn't blow up
        embeddings = self.model.encode(
            texts, 
            batch_size=32, 
            show_progress_bar=False, 
            normalize_embeddings=True # Important for Cosine Similarity
        )
        # Convert numpy array to list of lists for Qdrant
        return embeddings.tolist()

# Singleton instance (Model loading is heavy, load once)
bge_embedder = BGEEmbedder()