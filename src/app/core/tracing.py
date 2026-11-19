from contextlib import contextmanager
from langfuse import Langfuse
from app.core.config import settings

_langfuse_client: Langfuse | None = None
_initialized: bool = False


def get_langfuse_client() -> Langfuse | None:
    """Return a singleton Langfuse v2 client if keys are configured, else None."""
    global _langfuse_client, _initialized
    if _initialized:
        return _langfuse_client

    _initialized = True
    secret = settings.langfuse_secret_key.get_secret_value() if settings.langfuse_secret_key else ""
    if not settings.langfuse_public_key or not secret:
        _langfuse_client = None
        return None

    _langfuse_client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=secret,
        host=settings.langfuse_host,
    )
    return _langfuse_client


@contextmanager
def trace_context(
    name: str,
    input=None,
    metadata: dict | None = None,
    user_id: str | None = None,
):
    client = get_langfuse_client()
    if client is None:
        yield None
        return

    trace = client.trace(
        name=name,
        input=input,
        metadata=metadata,
        user_id=user_id,
    )
    try:
        yield trace
    except Exception as exc:
        trace.update(output={"error": str(exc)})
        raise
    finally:
        try:
            client.flush()
        except Exception:
            pass


@contextmanager
def span_context(
    trace,
    name: str,
    input=None,
    metadata: dict | None = None,
):
    if trace is None:
        yield None
        return

    span = trace.span(
        name=name,
        input=input,
        metadata=metadata,
    )
    try:
        yield span
    except Exception as exc:
        span.end(output={"error": str(exc)}, level="ERROR", status_message=str(exc))
        raise


@contextmanager
def generation_context(
    trace,
    name: str,
    model: str,
    input=None,
    metadata: dict | None = None,
):
    if trace is None:
        yield None
        return

    generation = trace.generation(
        name=name,
        model=model,
        input=input,
        metadata=metadata,
    )
    try:
        yield generation
    except Exception as exc:
        generation.end(output="LLM Generation failed", level="ERROR", status_message=str(exc))
        raise