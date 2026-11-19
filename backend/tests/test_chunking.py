from app.services.chunking.splitters import RecursiveChunker
from app.services.ingestion.schemas import ParsedDocument, RawFileMetadata, FileFormat


def test_recursive_chunking():
    # Mock document
    metadata = RawFileMetadata(
        tenant_id="test-tenant",
        original_filename="test.txt",
        object_key="key",
        file_format=FileFormat.TXT,
        size_bytes=1000,
        content_type="text/plain"
    )
    
    # Text with multiple paragraphs
    text = (
        "Hello world. This is the first sentence. " * 50 + "\n\n" + 
        "This is a new paragraph. It has its own sentences. " * 50
    )
    
    doc = ParsedDocument(metadata=metadata, text=text)
    
    # Initialize chunker with small size to force splitting
    chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk(doc)
    
    assert len(chunks) > 1
    for c in chunks:
        assert c.metadata.token_count <= 100
        assert c.metadata.document_id == metadata.document_id
        assert len(c.text) > 0

    print(f"Successfully created {len(chunks)} chunks.")