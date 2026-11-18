from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import Document, DocumentStatus
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.chunking.pipeline import ChunkingPipeline
from app.services.indexing.pipeline import IndexingPipeline
from app.core.logging import logger

@celery_app.task(name="process_document_task", bind=True)
def process_document_task(self, document_id: str):
    db = SessionLocal()
    try:
        # 1. Fetch Document from DB
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return f"Document {document_id} not found"

        # 2. Update status to PROCESSING
        doc.status = DocumentStatus.PROCESSING
        db.commit()

        logger.info(f"Started processing document: {doc.original_filename}")
        
        # 3. Pipeline 1: Ingestion
        ingestion = IngestionPipeline()
        parsed_doc = ingestion.ingest(
            tenant_id=doc.tenant_id,
            object_key=doc.object_key,
            original_filename=doc.original_filename,
            content_type="application/octet-stream" 
        )
        
        # 4. Pipeline 2: Chunking
        chunker = ChunkingPipeline()
        chunks = chunker.process(parsed_doc)
        
        # 5. Pipeline 3: Indexing (Embeddings + Qdrant)
        indexer = IndexingPipeline()
        indexer.process(chunks, tenant_id=doc.tenant_id)
        
        # 6. Update status to COMPLETED
        doc.status = DocumentStatus.COMPLETED
        db.commit()
        
        logger.info(f"Successfully processed {doc.original_filename} ({len(chunks)} chunks)")
        return "Success"

    except Exception as exc:
        logger.error(f"Failed to process document {document_id}: {str(exc)}")
        # Update status to FAILED
        if 'doc' in locals():
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc)
            db.commit()
        raise self.retry(exc=exc, countdown=10, max_retries=3)
    finally:
        db.close()