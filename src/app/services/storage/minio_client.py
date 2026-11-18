import io
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.core.exceptions import StorageError
from app.core.logging import logger


class MinioStorageClient:
    """Production-safe MinIO client with retries."""

    def __init__(self) -> None:
        self._client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key.get_secret_value(),
            secret_key=settings.minio_secret_key.get_secret_value(),
            secure=settings.minio_secure,
        )

    def ensure_buckets(self) -> None:
        """Idempotent: Creates buckets if they don't exist."""
        for bucket in (settings.minio_bucket_raw, settings.minio_bucket_processed):
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
                logger.info(
                    "Created MinIO bucket",
                    extra={"extra_fields": {"bucket": bucket}},
                )

    @retry(
        retry=retry_if_exception_type(StorageError),
        stop=stop_after_attempt(settings.ingestion_retry_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def upload_raw(self, object_key: str, data: bytes, content_type: str) -> str:
        try:
            self._client.put_object(
                bucket_name=settings.minio_bucket_raw,
                object_name=object_key,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return object_key
        except S3Error as exc:
            raise StorageError(f"MinIO upload failed for {object_key}: {exc}") from exc

    @retry(
        retry=retry_if_exception_type(StorageError),
        stop=stop_after_attempt(settings.ingestion_retry_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def download_raw(self, object_key: str) -> bytes:
        try:
            response: BinaryIO = self._client.get_object(
                bucket_name=settings.minio_bucket_raw,
                object_name=object_key,
            )
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as exc:
            raise StorageError(f"MinIO download failed for {object_key}: {exc}") from exc

# Singleton instance
minio_client = MinioStorageClient()