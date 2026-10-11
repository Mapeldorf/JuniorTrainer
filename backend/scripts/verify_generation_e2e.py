"""Verificacion manual de la tarea 6.7: un `trace_id` de Langfuse agrupa
las llamadas de los distintos agentes de UNA MISMA generacion.

El resto del grupo 6 (6.1-6.6) ya esta auto-verificado en el propio
contenedor contra tres agentes A2A desechables (ver design.md
"Orquestacion en FastAPI"); lo unico que falta y necesita servicios reales
es comprobar en Langfuse Cloud de verdad que las llamadas quedan agrupadas.

No hace falta `docker-compose` (grupo 7, todavia no existe): esta
verificacion llama a `run_generation()` directamente, sin pasar por
`POST /generations` ni por ningun servidor HTTP del backend, y sin
repositorio (asi que el agente de codigo tampoco hace falta tenerlo
arrancado) -- solo agente web y agente de ejercicios.

Preparacion (tres terminales, cada uno con su propio venv y su .env real):
  1. agents/web:       uvicorn app.main:app --host 0.0.0.0 --port 8010
  2. agents/exercises: uvicorn app.main:app --host 0.0.0.0 --port 8012
  3. El .env de la raiz del repo con SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY
     y LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY/LANGFUSE_BASE_URL reales, y
     ya debe existir al menos un profile con role='tech_lead' (si no, usa
     antes `python -m scripts.seed_tech_lead`).

Uso (desde backend/, con el venv del backend activo):
    AGENT_WEB_URL=http://127.0.0.1:8010/ AGENT_EXERCISES_URL=http://127.0.0.1:8012/ \
    python -m scripts.verify_generation_e2e

(Los valores por defecto de AGENT_WEB_URL/AGENT_EXERCISES_URL son los
nombres de servicio de docker-compose, que todavia no existe -- hay que
sobreescribirlos a localhost para esta verificacion suelta.)
"""

import asyncio

import app.orchestrator as orchestrator
import app.tracing as tracing
from app.supabase_client import get_admin_client

_original_new_trace_id = tracing.new_trace_id
_captured: dict = {}


def _capturing_new_trace_id() -> str:
    trace_id = _original_new_trace_id()
    _captured["trace_id"] = trace_id
    return trace_id


# orchestrator.py importa `new_trace_id` por nombre (`from app.tracing import
# new_trace_id`), asi que hay que parchear la referencia que usa el propio
# modulo orchestrator, no solo app.tracing.new_trace_id.
orchestrator.new_trace_id = _capturing_new_trace_id


async def main() -> None:
    admin = get_admin_client()

    tech_lead = (
        admin.table("profile").select("id, email").eq("role", "tech_lead").limit(1).execute().data
    )
    if not tech_lead:
        raise SystemExit(
            "no hay ningun profile con role='tech_lead' todavia -- "
            "crea uno con `python -m scripts.seed_tech_lead` primero"
        )
    tech_lead_id = tech_lead[0]["id"]
    print(f"usando tech_lead: {tech_lead[0]['email']} ({tech_lead_id})")

    result = (
        admin.table("generation")
        .insert(
            {
                "repo_name": "",
                "technologies": "Git",
                "kind": "knowledge",
                "status": "generating",
                "created_by": tech_lead_id,
            }
        )
        .execute()
    )
    generation_id = result.data[0]["id"]
    print(f"generation_id: {generation_id}")

    await orchestrator.run_generation(generation_id, ["Git"], None, "knowledge", 1)

    row = (
        admin.table("generation")
        .select("status, error_message")
        .eq("id", generation_id)
        .limit(1)
        .execute()
        .data[0]
    )
    print(f"status final: {row}")
    assert row["status"] == "ready", f"se esperaba 'ready', la generacion quedo en: {row}"

    candidates = (
        admin.table("exercise")
        .select("id, type, statement")
        .eq("generation_id", generation_id)
        .execute()
        .data
    )
    print(f"candidatos insertados: {len(candidates)}")
    assert len(candidates) == 1, candidates

    trace_id = _captured.get("trace_id")
    print()
    if trace_id:
        from langfuse import get_client

        tracing.init_client()
        print(f"trace_id: {trace_id}")
        print(f"URL: {get_client().get_trace_url(trace_id=trace_id)}")
    print(
        "OK: revisa esa traza en Langfuse Cloud (puede tardar unos segundos en aparecer) y comprueba "
        "que 'orquestacion' (backend), 'agente-web' y 'agente-exercises' aparecen bajo el mismo trace_id"
    )


if __name__ == "__main__":
    asyncio.run(main())
