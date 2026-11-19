import asyncio
import json
from pathlib import Path

from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

from app.core.config import settings
from app.services.generation.pipeline import GenerationPipeline
from app.services.retrieval.pipeline import RetrievalPipeline


async def main() -> None:
    dataset_path = Path("tests/eval_golden_policy.json")
    samples = json.loads(dataset_path.read_text(encoding="utf-8"))

    retriever = RetrievalPipeline()
    generator = GenerationPipeline()

    groq_client = AsyncOpenAI(
        api_key=settings.groq_api_key.get_secret_value(),
        base_url="https://api.groq.com/openai/v1",
        max_retries=6,
    )
    judge_llm = llm_factory(
        settings.llm_model_name,
        client=groq_client,
    )

    faithfulness = Faithfulness(llm=judge_llm)
    context_precision = ContextPrecision(llm=judge_llm)
    context_recall = ContextRecall(llm=judge_llm)

    scores = {
        "faithfulness": [],
        "context_precision": [],
        "context_recall": [],
    }

    for item in samples:
        question = item["user_input"]
        reference = item["reference"]

        contexts_raw = retriever.retrieve(query=question, tenant_id="test-tenant-123")
        retrieved_contexts = [c["text"] for c in contexts_raw]
        answer = generator.generate_answer(query=question, contexts=contexts_raw)

        f_res = await faithfulness.ascore(
            user_input=question,
            response=answer,
            retrieved_contexts=retrieved_contexts,
        )
        cp_res = await context_precision.ascore(
            user_input=question,
            reference=reference,
            retrieved_contexts=retrieved_contexts,
        )
        cr_res = await context_recall.ascore(
            user_input=question,
            reference=reference,
            retrieved_contexts=retrieved_contexts,
        )

        scores["faithfulness"].append(float(f_res.value))
        scores["context_precision"].append(float(cp_res.value))
        scores["context_recall"].append(float(cr_res.value))

        print(f"Q: {question}")
        print(f"  Answer: {answer}")
        print(
            f"  Faithfulness={f_res.value:.2f} | "
            f"CtxPrec={cp_res.value:.2f} | CtxRec={cr_res.value:.2f}\n"
        )

    print("=== AVERAGE RAGAS SCORES ===")
    for metric, vals in scores.items():
        avg = sum(vals) / len(vals) if vals else 0.0
        print(f"{metric}: {avg:.4f}")


if __name__ == "__main__":
    asyncio.run(main())