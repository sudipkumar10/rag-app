from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.services.storage.minio_client import minio_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)
    logger.info("Starting application...")
    
    try:
        minio_client.ensure_buckets()
        logger.info("MinIO buckets verified")
    except Exception as e:
        logger.error(f"Failed to connect to MinIO: {e}")
        
    yield
    logger.info("Shutting down application")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}