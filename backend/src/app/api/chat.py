from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.tracing import trace_context
from app.services.generation.pipeline import GenerationPipeline
from app.services.retrieval.pipeline import RetrievalPipeline
from app.services.retrieval.router import QueryRouter  

router = APIRouter()
query_router = QueryRouter()  
class ChatRequest(BaseModel):
    tenant_id: str
    query: str
class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    try:
        # 1. Intent Routing Check (Fast path for greetings)
        intent = query_router.get_intent(request.query)

        with trace_context(
            name="rag-chat-query",
            input={"tenant_id": request.tenant_id, "query": request.query},
            metadata={"tenant_id": request.tenant_id, "intent": intent},
            user_id=request.tenant_id,
        ) as trace:
            
            # --- FAST PATH: Handle Greetings & Thanks ---
            if intent == "GREETING":
                answer = "Hello! I am your AI assistant. How can I help you with your documents today?"
                sources = []
                if trace is not None:
                    trace.update(output={"answer": answer, "sources": sources, "type": "fast_path"})
                return ChatResponse(answer=answer, sources=sources)

            if intent == "THANKS":
                answer = "You're welcome! Let me know if you have any more questions."
                sources = []
                if trace is not None:
                    trace.update(output={"answer": answer, "sources": sources, "type": "fast_path"})
                return ChatResponse(answer=answer, sources=sources)

            # --- NORMAL PATH: RAG Flow ---
            # 2. Retrieve
            retriever = RetrievalPipeline()
            contexts = retriever.retrieve(
                query=request.query,
                tenant_id=request.tenant_id,
                trace=trace,
            )

            # 3. Generate
            generator = GenerationPipeline()
            answer = generator.generate_answer(
                query=request.query,
                contexts=contexts,
                trace=trace,
            )

            # 4. Extract unique sources
            sources = list({ctx["filename"] for ctx in contexts})

            if trace is not None:
                trace.update(output={"answer": answer, "sources": sources, "type": "rag"})

        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))