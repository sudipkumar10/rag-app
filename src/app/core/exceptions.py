"""Domain exception hierarchy — upstream decides retry vs fail-fast."""


class RAGBaseError(Exception):
    pass


class StorageError(RAGBaseError):
    """Retryable — MinIO/S3 transient failure."""


class UnsupportedFileTypeError(RAGBaseError):
    """Permanent — extension not allowed."""


class FileTooLargeError(RAGBaseError):
    """Permanent — size limit exceeded."""


class DocumentParseError(RAGBaseError):
    """Permanent — content unparseable."""


class EmptyDocumentError(RAGBaseError):
    """Permanent — no usable text after parse."""