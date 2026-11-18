from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.services.ingestion.schemas import RawFileMetadata


class ChunkMetadata(BaseModel):
    """Metadata attached to every chunk for tracing and filtering."""
    document_id: UUID
    tenant_id: str
    original_filename: str
    chunk_index: int
    total_chunks: int
    token_count: int
    page_number: int | None = None


class Chunk(BaseModel):
    """The actual chunk object."""
    chunk_id: UUID = Field(default_factory=uuid4)
    text: str
    metadata: ChunkMetadata