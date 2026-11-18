from abc import ABC, abstractmethod
from app.services.chunking.schemas import Chunk
from app.services.ingestion.schemas import ParsedDocument


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        """Convert a ParsedDocument into a list of Chunks."""
        raise NotImplementedError