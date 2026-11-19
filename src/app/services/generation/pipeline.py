from groq import Groq
from app.core.config import settings
from app.core.logging import logger

class GenerationPipeline:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key.get_secret_value())

    def generate_answer(self, query: str, contexts: list[dict]) -> str:
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
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=settings.llm_model_name,
                temperature=0.1, # Low temperature for factual answers
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM Generation failed: {str(e)}")
            return "Sorry, I am facing technical issues right now. Please try again later."