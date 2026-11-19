from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.retrieval.pipeline import RetrievalPipeline
from app.services.generation.pipeline import GenerationPipeline

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
        # 1. Retrieve
        retriever = RetrievalPipeline()
        contexts = retriever.retrieve(query=request.query, tenant_id=request.tenant_id)
        
        # 2. Generate
        generator = GenerationPipeline()
        answer = generator.generate_answer(query=request.query, contexts=contexts)
        
        # 3. Extract unique sources
        sources = list(set([ctx['filename'] for ctx in contexts]))
        
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))