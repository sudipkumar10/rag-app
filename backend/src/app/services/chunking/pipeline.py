from app.services.chunking.base import BaseChunker
from app.services.chunking.splitters import RecursiveChunker
from app.services.chunking.schemas import Chunk
from app.services.ingestion.schemas import ParsedDocument
from app.core.logging import logger


class ChunkingPipeline:
    def __init__(self, chunker: BaseChunker | None = None):
        # Default chunker if not provided
        self.chunker = chunker or RecursiveChunker(chunk_size=500, chunk_overlap=50)

    def process(self, document: ParsedDocument) -> list[Chunk]:
        """
        Takes a ParsedDocument and returns a list of Chunks.
        """
        logger.info(
            "Starting chunking process",
            extra={"extra_fields": {"document_id": str(document.metadata.document_id)}}
        )
        
        chunks = self.chunker.chunk(document)
        
        return chunks