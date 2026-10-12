"""Verificacion manual de la tarea 3.3: trace_id de Langfuse.

El backend (grupo 5, `app/answer_orchestrator.py`) es quien normalmente
pondria `trace_id` en los metadatos del mensaje A2A. Sin el, este script
simula su papel: genera un `trace_id` el mismo y llama directamente a la
logica de negocio (sin pasar por el transporte A2A) exactamente como lo
haria `EvaluatorAgentExecutor.execute()` -- ver app/executor.py.

Uso (desde agents/evaluator/, con LITELLM_MASTER_KEY/EVALUATOR_MODEL/
EVALUATOR_API_KEY/LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY/LANGFUSE_BASE_URL
en el .env de la raiz del repo, LiteLLM corriendo):
    python -m scripts.verify_trace_id
"""

import asyncio
import logging

from app.service import evaluate_answer
from app.tracing import get_client, init_client, new_trace_id, record_task

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    init_client()
    client = get_client()

    trace_id = new_trace_id()
    result = await evaluate_answer(
        statement="Escribe una funcion que sume dos numeros.",
        code=[],
        expected_answer="return a + b",
        student_answer="return a + b",
        trace_id=trace_id,
    )
    record_task(trace_id, result.verdict)
    print(f"trace_id={trace_id}, verdict={result.verdict}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id)}")
    client.flush()


if __name__ == "__main__":
    asyncio.run(main())
