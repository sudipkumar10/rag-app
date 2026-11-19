from groq import Groq
from app.core.config import settings
from app.core.logging import logger
from app.core.tracing import generation_context


class GenerationPipeline:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key.get_secret_value())

    def generate_answer(self, query: str, contexts: list[dict], trace=None) -> str:
        if not contexts:
            return "I could not find any relevant information in the provided documents to answer your question."

        # 1. Build Context String
        context_text = ""
        for i, ctx in enumerate(contexts):
            context_text += f"\n--- Source {i+1} ({ctx['filename']}) ---\n{ctx['text']}\n"

        # 2. System Prompt (Guardrails included)
        system_prompt = (
            "You are a helpful AI assistant. Answer the user's question using ONLY the provided context. "
            "If the answer is not in the context, say 'I don't have enough information to answer that.' "
            "Do not hallucinate or use outside knowledge. Keep the answer concise."
        )

        user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}"

        # 3. Call LLM
        with generation_context(
            trace=trace,
            name="groq-generation",
            model=settings.llm_model_name,
            input={"system_prompt": system_prompt, "user_prompt": user_prompt},
            metadata={"contexts_count": len(contexts), "sources": [c["filename"] for c in contexts]},
        ) as generation:
            try:
                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=settings.llm_model_name,
                    temperature=0.1,
                    max_tokens=1024,
                )
                answer = response.choices[0].message.content
                if generation is not None:
                    usage_payload = None
                    if getattr(response, "usage", None):
                        usage_payload = {
                            "input": response.usage.prompt_tokens,
                            "output": response.usage.completion_tokens,
                            "total": response.usage.total_tokens,
                        }
                    generation.end(output=answer, usage=usage_payload)
                return answer
            except Exception as e:
                logger.error(f"LLM Generation failed: {str(e)}")
                if generation is not None:
                    generation.end(output="LLM Generation failed", level="ERROR", status_message=str(e))
                return "Sorry, I am facing technical issues right now. Please try again later."