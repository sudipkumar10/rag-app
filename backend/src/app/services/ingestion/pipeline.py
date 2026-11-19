from pathlib import Path
from app.core.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.services.ingestion.loaders import LOADER_REGISTRY
from app.services.ingestion.schemas import FileFormat, ParsedDocument, RawFileMetadata
from app.services.storage.minio_client import minio_client

_EXT_TO_FORMAT = {
    ".txt": FileFormat.TXT, ".pdf": FileFormat.PDF,
    ".csv": FileFormat.CSV, ".xlsx": FileFormat.EXCEL, ".xls": FileFormat.EXCEL,
}

class IngestionPipeline:
    def __init__(self) -> None:
        self.storage = minio_client

    def validate(self, filename: str, size_bytes: int) -> FileFormat:
        ext = Path(filename).suffix.lower()
        if ext not in settings.ingestion_allowed_extensions:
            raise UnsupportedFileTypeError(f"Extension '{ext}' not allowed.")
        
        max_bytes = settings.ingestion_max_file_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise FileTooLargeError(f"File too large: {size_bytes} bytes")
        
        return _EXT_TO_FORMAT[ext]

    def ingest(self, tenant_id: str, object_key: str, original_filename: str, content_type: str) -> ParsedDocument:
        raw_bytes = self.storage.download_raw(object_key)
        file_format = self.validate(original_filename, len(raw_bytes))

        metadata = RawFileMetadata(
            tenant_id=tenant_id, original_filename=original_filename,
            object_key=object_key, file_format=file_format,
            size_bytes=len(raw_bytes), content_type=content_type,
        )

        ext = Path(original_filename).suffix.lower()
        loader_cls = LOADER_REGISTRY.get(ext)
        if not loader_cls:
            raise UnsupportedFileTypeError(f"No loader for '{ext}'")

        return loader_cls().load(raw_bytes, metadata)