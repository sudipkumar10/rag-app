import io
import pymupdf
import pandas as pd
from pathlib import Path
from typing import Type
from app.core.exceptions import DocumentParseError, EmptyDocumentError
from app.services.ingestion.base import BaseLoader
from app.services.ingestion.schemas import FileFormat, ParsedDocument, RawFileMetadata


class TxtLoader(BaseLoader):
    supported_extensions = (".txt",)

    def load(self, raw_bytes: bytes, metadata: RawFileMetadata) -> ParsedDocument:
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = raw_bytes.decode("latin-1", errors="replace")
        
        text = text.strip()
        if not text:
            raise EmptyDocumentError(f"TXT {metadata.original_filename} is empty")
        return ParsedDocument(metadata=metadata, text=text)


class PdfLoader(BaseLoader):
    supported_extensions = (".pdf",)

    def load(self, raw_bytes: bytes, metadata: RawFileMetadata) -> ParsedDocument:
        try:
            doc = pymupdf.open(stream=raw_bytes, filetype="pdf")
        except Exception as exc:
            raise DocumentParseError(f"PDF open failed: {exc}") from exc

        page_texts = []
        for page in doc:
            page_texts.append(page.get_text("text").strip())
        doc.close()

        full_text = "\n\n".join(t for t in page_texts if t).strip()
        if not full_text:
            raise EmptyDocumentError(f"PDF {metadata.original_filename} yielded no text")

        return ParsedDocument(
            metadata=metadata,
            text=full_text,
            page_count=len(page_texts),
        )


class CsvLoader(BaseLoader):
    supported_extensions = (".csv",)

    def load(self, raw_bytes: bytes, metadata: RawFileMetadata) -> ParsedDocument:
        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), dtype=str, keep_default_na=False)
        except Exception as exc:
            raise DocumentParseError(f"CSV parse failed: {exc}") from exc

        if df.empty:
            raise EmptyDocumentError(f"CSV {metadata.original_filename} has no rows")

        row_texts = []
        for _, row in df.iterrows():
            row_text = " | ".join(f"{col}: {row[col]}" for col in df.columns if row[col])
            if row_text:
                row_texts.append(row_text)

        return ParsedDocument(
            metadata=metadata,
            text="\n".join(row_texts).strip(),
            page_count=len(df),
        )


class ExcelLoader(BaseLoader):
    supported_extensions = (".xlsx", ".xls")

    def load(self, raw_bytes: bytes, metadata: RawFileMetadata) -> ParsedDocument:
        try:
            sheets = pd.read_excel(io.BytesIO(raw_bytes), sheet_name=None, dtype=str, keep_default_na=False)
        except Exception as exc:
            raise DocumentParseError(f"Excel parse failed: {exc}") from exc

        sheet_texts = []
        for sheet_name, df in sheets.items():
            if df.empty: continue
            row_texts = []
            for _, row in df.iterrows():
                row_text = " | ".join(f"{col}: {row[col]}" for col in df.columns if row[col])
                if row_text:
                    row_texts.append(row_text)
            if row_texts:
                sheet_texts.append(f"### Sheet: {sheet_name}\n" + "\n".join(row_texts))

        full_text = "\n\n".join(sheet_texts).strip()
        if not full_text:
            raise EmptyDocumentError(f"Excel {metadata.original_filename} yielded no text")

        return ParsedDocument(metadata=metadata, text=full_text, page_count=len(sheets))


# Registry
LOADER_REGISTRY: dict[str, Type[BaseLoader]] = {
    ".txt": TxtLoader,
    ".pdf": PdfLoader,
    ".csv": CsvLoader,
    ".xlsx": ExcelLoader,
    ".xls": ExcelLoader,
}