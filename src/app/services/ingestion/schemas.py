from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FileFormat(str, Enum):
    TXT = "txt"
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


class RawFileMetadata(BaseModel):
    document_id: UUID = Field(default_factory=uuid4)
    tenant_id: str
    original_filename: str
    object_key: str
    file_format: FileFormat
    size_bytes: int
    content_type: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ParsedDocument(BaseModel):
    metadata: RawFileMetadata
    text: str
    structured: dict[str, Any] = Field(default_factory=dict)
    page_count: int | None = None
    parse_warnings: list[str] = Field(default_factory=list)