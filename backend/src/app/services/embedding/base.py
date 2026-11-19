from abc import ABC, abstractmethod

class BaseEmbedder(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Convert a list of strings into a list of vector embeddings."""
        raise NotImplementedError