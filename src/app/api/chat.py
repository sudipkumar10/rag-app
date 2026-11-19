from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.tracing import trace_context
from app.services.generation.pipeline import GenerationPipeline
from app.services.retrieval.pipeline import RetrievalPipeline

router = APIRouter()


class ChatRequest(BaseModel):
    tenant_id: str
    query: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    try:
        with trace_context(
            name="rag-chat-query",
            input={"tenant_id": request.tenant_id, "query": request.query},
            metadata={"tenant_id": request.tenant_id},
            user_id=request.tenant_id,
        ) as trace:
            # 1. Retrieve
            retriever = RetrievalPipeline()
            contexts = retriever.retrieve(
                query=request.query,
                tenant_id=request.tenant_id,
                trace=trace,
            )

            # 2. Generate
            generator = GenerationPipeline()
            answer = generator.generate_answer(
                query=request.query,
                contexts=contexts,
                trace=trace,
            )

            # 3. Extract unique sources
            sources = list({ctx["filename"] for ctx in contexts})

            if trace is not None:
                trace.update(output={"answer": answer, "sources": sources})

        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))