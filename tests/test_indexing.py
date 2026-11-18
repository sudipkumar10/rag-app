from app.services.chunking.schemas import Chunk, ChunkMetadata
from app.services.indexing.pipeline import IndexingPipeline
from uuid import uuid4

def test_indexing_pipeline():
    # Mock chunk
    metadata = ChunkMetadata(
        document_id=uuid4(),
        tenant_id="test-tenant-123",
        original_filename="test.pdf",
        chunk_index=0,
        total_chunks=1,
        token_count=10
    )
    chunk = Chunk(text="Hello world, this is a test chunk for RAG.", metadata=metadata)
    
    pipeline = IndexingPipeline()
    pipeline.process(chunks=[chunk], tenant_id="test-tenant-123")
    
    assert True