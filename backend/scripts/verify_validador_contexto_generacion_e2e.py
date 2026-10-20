"""Reproduccion manual (end-to-end, agentes reales) del caso original que
motivo el change `validador-contexto-generacion`: una generacion de
conocimiento con una tecnologia que YA esta en el catalogo (p. ej.
"RxJS en Angular") fallaba en el paso de validacion porque el validador la
marcaba como "duplicado de si misma".

Mismo patron que `verify_generation_e2e.py`: llama a `run_generation()`
directamente (sin pasar por `POST /generations` ni por ningun servidor
HTTP del backend), pero SI contra el agente validador real por A2A -- hace
falta tenerlo arrancado (docker-compose, o `uvicorn app.main:app --port
8015` en `agents/validator/`) y el `.env` real de la raiz.

No necesita agente web ni agente de codigo: se corta la generacion justo
despues del validador comprobando el estado final (no llega a invocarlos
porque el `kind="knowledge"` sin repo solo necesita el agente web, que aqui
puede fallar sin que la generacion falle -- ver orchestrator.py `_call_web`,
"degradacion" -- asi que una generacion que llegue a `ready` o a un error
DISTINTO del de duplicados ya demuestra que el paso de validacion no es la
causa).

Uso (desde backend/, con el venv del backend activo, agente validador y
LiteLLM corriendo, AGENT_VALIDATOR_URL apuntando a el):
    python -m scripts.verify_validador_contexto_generacion_e2e
"""

import asyncio

from app.orchestrator import run_generation
from app.supabase_client import get_admin_client

# "RxJS en Angular" esta sembrada por 0009_technology_catalog.sql en el
# entorno de desarrollo real; si no estuviera, cualquier otra tecnologia ya
# existente en el catalogo reproduce el mismo caso.
_TECHNOLOGY = "RxJS en Angular"


async def main() -> None:
    admin = get_admin_client()

    tech_lead_rows = (
        admin.table("profile").select("id, email").eq("role", "tech_lead").limit(1).execute().data
    )
    if not tech_lead_rows:
        raise SystemExit(
            "no hay ningun profile con role='tech_lead' todavia -- "
            "crea uno con `python -m scripts.seed_tech_lead` primero"
        )
    tech_lead_id = tech_lead_rows[0]["id"]

    existing = (
        admin.table("technology").select("id").ilike("name", _TECHNOLOGY).limit(1).execute().data
    )
    if not existing:
        raise SystemExit(
            f"'{_TECHNOLOGY}' no esta en el catalogo de este entorno -- "
            "usa una tecnologia que ya exista en public.technology"
        )

    result = (
        admin.table("generation")
        .insert(
            {
                "repo_name": "",
                "technologies": _TECHNOLOGY,
                "kind": "knowledge",
                "status": "generating",
                "created_by": tech_lead_id,
            }
        )
        .execute()
    )
    generation_id = result.data[0]["id"]
    print(f"generacion creada: {generation_id}")

    await run_generation(generation_id, [_TECHNOLOGY], None, None, "knowledge", 1, tech_lead_id)

    row = (
        admin.table("generation").select("status, error_message").eq("id", generation_id).execute().data[0]
    )
    print(f"estado final: {row['status']!r} error_message={row.get('error_message')!r}")

    if row["status"] == "error" and row.get("error_message") and "duplicad" in row["error_message"].lower():
        raise AssertionError(
            "la generacion sigue fallando por duplicado semantico -- el fix no esta aplicado"
        )
    print("OK: la generacion ya no falla en el paso de validacion por 'duplicado de si misma'")


if __name__ == "__main__":
    asyncio.run(main())
