import tiktoken
from app.services.chunking.base import BaseChunker
from app.services.chunking.schemas import Chunk, ChunkMetadata
from app.services.ingestion.schemas import ParsedDocument
from app.core.logging import logger


class RecursiveChunker(BaseChunker):
    """
    Production-grade recursive chunker.
    Splits by paragraphs, then sentences, then words.
    Ensures exact token limits and overlap.
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Order matters: Try paragraph -> line -> sentence -> word -> char
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def _count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        final_chunks = []
        separator = separators[-1]
        new_separators = []
        
        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                break
            if _s in text:
                separator = _s
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)
        
        current_chunk = []
        current_length = 0

        for s in splits:
            token_count = self._count_tokens(s)
            sep_len = self._count_tokens(separator) if current_chunk else 0
            
            # Check if adding this split exceeds chunk_size
            if current_length + token_count + sep_len > self.chunk_size:
                if current_chunk:
                    final_chunks.append(separator.join(current_chunk))
                    
                    # FIX: Exact overlap reduction. Pop until size <= chunk_overlap
                    # AND ensure adding the new `s` won't exceed chunk_size.
                    while (current_length > self.chunk_overlap or 
                           current_length + token_count + (self._count_tokens(separator) if current_chunk else 0) > self.chunk_size) and current_chunk:
                        current_chunk.pop(0)
                        if current_chunk:
                            # Recalculate exact length after popping
                            current_length = self._count_tokens(separator.join(current_chunk))
                        else:
                            current_length = 0
                
                # If single split is still too large, recurse
                if token_count > self.chunk_size and new_separators:
                    final_chunks.extend(self._split_text(s, new_separators))
                    current_chunk = []
                    current_length = 0
                else:
                    current_chunk.append(s)
                    current_length = self._count_tokens(separator.join(current_chunk)) if current_chunk else token_count
            else:
                current_chunk.append(s)
                current_length += token_count + sep_len

        if current_chunk:
            final_chunks.append(separator.join(current_chunk))

        return final_chunks

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        raw_chunks = self._split_text(document.text, self.separators)
        raw_chunks = [c.strip() for c in raw_chunks if c.strip()]
        
        chunks = []
        total_chunks = len(raw_chunks)
        
        for index, text in enumerate(raw_chunks):
            metadata = ChunkMetadata(
                document_id=document.metadata.document_id,
                tenant_id=document.metadata.tenant_id,
                original_filename=document.metadata.original_filename,
                chunk_index=index,
                total_chunks=total_chunks,
                token_count=self._count_tokens(text),
                page_number=None 
            )
            chunks.append(Chunk(text=text, metadata=metadata))
            
        logger.info(
            "Document chunked successfully",
            extra={
                "extra_fields": {
                    "document_id": str(document.metadata.document_id),
                    "total_chunks": total_chunks,
                }
            }
        )
        return chunks