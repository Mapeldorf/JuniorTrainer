"""Verificacion manual de la tarea 3.5: memoria corta por tarea.

Comprueba que `research_with_checkpoint()` borra siempre el checkpoint de
la tarea al terminar, tanto si la tarea acaba bien (Ready) como si falla
(error) -- sin dejar nada en las tablas `memory.checkpoints`/
`memory.checkpoint_blobs`/`memory.checkpoint_writes` de Postgres.

Uso (desde agents/web/, con las mismas variables de entorno que
verify_memory_cache.py: TAVILY_API_KEY, LITELLM_MASTER_KEY, AGENTS_PG_*,
AGENTS_MEMORY_PASSWORD, SUPABASE_PROJECT_REF, LiteLLM corriendo):
    python -m scripts.verify_short_term_memory
"""

import asyncio
import logging
import uuid

from app.checkpoint import count_checkpoints, research_with_checkpoint

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Caso 1: tarea que termina bien (Ready).
    ok_task_id = f"verify-ok-{uuid.uuid4()}"
    result = await research_with_checkpoint(ok_task_id, ["React"])
    print(f"tarea OK: memory_hit={result.memory_hit}, {len(result.sources)} fuentes")

    remaining_ok = await count_checkpoints(ok_task_id)
    print(f"checkpoints restantes tras tarea OK: {remaining_ok}")
    assert remaining_ok == 0, "la tarea OK no deberia dejar checkpoints"

    # Caso 2: tarea que falla (error) -- research() lanza ValueError si no
    # hay tecnologias (ver app/service.py).
    err_task_id = f"verify-err-{uuid.uuid4()}"
    try:
        await research_with_checkpoint(err_task_id, [])
    except ValueError as exc:
        print(f"tarea con error: excepcion propagada correctamente ({exc})")
    else:
        raise AssertionError("se esperaba un ValueError para tecnologias=[]")

    remaining_err = await count_checkpoints(err_task_id)
    print(f"checkpoints restantes tras tarea con error: {remaining_err}")
    assert remaining_err == 0, "la tarea con error no deberia dejar checkpoints"

    print("OK: la memoria corta se borro en ambos casos (Ready y error).")


if __name__ == "__main__":
    asyncio.run(main())
