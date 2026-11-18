from abc import ABC, abstractmethod
from app.services.ingestion.schemas import ParsedDocument, RawFileMetadata


class BaseLoader(ABC):
    supported_extensions: tuple[str, ...] = ()

    @abstractmethod
    def load(self, raw_bytes: bytes, metadata: RawFileMetadata) -> ParsedDocument:
        """Parse raw bytes into a ParsedDocument."""
        raise NotImplementedError