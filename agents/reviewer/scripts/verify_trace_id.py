"""Verificacion manual de la tarea 4.3: trace_id de Langfuse.

Analogo a `agents/evaluator/scripts/verify_trace_id.py` -- ver ese
fichero para la explicacion completa.

Uso (desde agents/reviewer/, con LITELLM_MASTER_KEY/REVIEWER_MODEL/
REVIEWER_API_KEY/LANGFUSE_* en el .env de la raiz del repo, LiteLLM
corriendo):
    python -m scripts.verify_trace_id
"""

import asyncio
import logging

from app.service import review_justification
from app.tracing import get_client, init_client, new_trace_id, record_task

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    init_client()
    client = get_client()

    trace_id = new_trace_id()
    result = await review_justification(
        statement="Escribe una funcion que sume dos numeros.",
        student_answer="return a + b",
        verdict="correct",
        justification="La respuesta suma a y b correctamente.",
        trace_id=trace_id,
    )
    record_task(trace_id)
    print(f"trace_id={trace_id}, justification={result.justification!r}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id)}")
    client.flush()


if __name__ == "__main__":
    asyncio.run(main())
