"""Verificacion manual del requisito "El agente de ejercicios no repite
temas ya propuestos" tras el change `eliminar-memoria-agente-ejercicios`.

El mecanismo ya no es una memoria propia del agente (eliminada): ahora
`search_saved_exercises` (ver app/tools/saved_exercises.py) es la UNICA
fuente de "enunciados a evitar", leyendo directamente `public.exercise`
(guardados y eliminados). Este script siembra un ejercicio guardado y
otro eliminado directamente en esa tabla (via la API REST de Supabase
con la service_role key, igual que lo haria el backend real), lanza una
generacion real y comprueba que `memory_hit` es `true` y que los
enunciados generados aparecen impresos para compararlos a ojo contra los
sembrados (no se puede verificar en codigo que el modelo evita el TEMA,
solo que el prompt recibio la instruccion).

La siembra y la limpieza usan SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY del
.env de la raiz del repo (no son credenciales del agente: el agente
sigue usando solo el rol de solo lectura `agents_exercise_reader`).

Uso (desde agents/exercises/, con AGENT_EXERCISES_LITELLM_KEY/AGENTS_PG_*/
AGENTS_EXERCISE_READER_PASSWORD/SUPABASE_PROJECT_REF/SUPABASE_URL/
SUPABASE_SERVICE_ROLE_KEY en el .env de la raiz del repo, LiteLLM corriendo):
    python -m scripts.verify_no_repeated_themes
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values

from app.service import generate_exercises

logging.basicConfig(level=logging.INFO)

_ENV = dotenv_values(Path(__file__).resolve().parent.parent.parent.parent / ".env")
_SUPABASE_URL = _ENV["SUPABASE_URL"]
_SERVICE_ROLE_KEY = _ENV["SUPABASE_SERVICE_ROLE_KEY"]
_HEADERS = {
    "apikey": _SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

_WEB_RESULT = {
    "summary": (
        "## Python\nPython es un lenguaje interpretado, de tipado dinamico, "
        "con soporte nativo para programacion orientada a objetos, "
        "funcional y estructurada. Usa indentacion para delimitar bloques."
    ),
    "sources": [],
    "memory_hit": False,
}


def _seed_exercise(
    client: httpx.Client, *, name: str, statement: str, saved: bool, deleted: bool
) -> tuple[str, str]:
    """Crea una `generation` minima y un `exercise` colgando de ella.

    Reutiliza el primer perfil que encuentra como `created_by` (el valor
    no importa para este requisito, solo que sea un id valido). Devuelve
    `(generation_id, exercise_id)` para poder limpiarlos despues.
    """
    profile = client.get("/rest/v1/profile?select=id&limit=1").json()
    if not profile:
        raise RuntimeError("no hay ningun profile en la base de datos para usar como created_by")
    created_by = profile[0]["id"]

    generation = client.post(
        "/rest/v1/generation",
        json={
            "technologies": "Python",
            "kind": "knowledge",
            "status": "ready",
            "created_by": created_by,
        },
    ).json()[0]

    # `name` es NOT NULL desde la migracion 0006 (change `ejercicios-con-nombre`):
    # sin el, el insert falla con 23502 y la siembra no llega a ocurrir.
    # `deleted_at` se manda como marca de tiempo ISO real, no como "now()":
    # PostgREST lo pasa como literal y Postgres no acepta 'now()' como
    # timestamptz.
    response = client.post(
        "/rest/v1/exercise",
        json={
            "generation_id": generation["id"],
            "type": "knowledge",
            "name": name,
            "statement": statement,
            "saved": saved,
            "deleted_at": datetime.now(timezone.utc).isoformat() if deleted else None,
        },
    )
    if response.status_code >= 400:
        raise RuntimeError(f"no se pudo sembrar el ejercicio ({response.status_code}): {response.text}")
    exercise = response.json()[0]

    return generation["id"], exercise["id"]


def _delete_seed(client: httpx.Client, generation_id: str, exercise_id: str) -> None:
    client.delete(f"/rest/v1/exercise?id=eq.{exercise_id}")
    client.delete(f"/rest/v1/generation?id=eq.{generation_id}")


async def main() -> None:
    marker = uuid.uuid4().hex[:8]
    saved_statement = f"[verify-{marker}] Explica que hace el decorador @staticmethod en una clase Python."
    deleted_statement = f"[verify-{marker}] Explica la diferencia entre una tupla y una lista en Python."

    with httpx.Client(base_url=_SUPABASE_URL, headers=_HEADERS, timeout=10.0) as client:
        gen_id_1, ex_id_1 = _seed_exercise(
            client,
            name=f"[verify-{marker}] Decorador staticmethod",
            statement=saved_statement,
            saved=True,
            deleted=False,
        )
        gen_id_2, ex_id_2 = _seed_exercise(
            client,
            name=f"[verify-{marker}] Tupla frente a lista",
            statement=deleted_statement,
            saved=False,
            deleted=True,
        )
        try:
            result = await generate_exercises("knowledge", 2, _WEB_RESULT, None)
        finally:
            _delete_seed(client, gen_id_1, ex_id_1)
            _delete_seed(client, gen_id_2, ex_id_2)

    print(f"memory_hit={result.memory_hit}")
    for c in result.candidates:
        print(f"  - {c.statement}")

    assert result.memory_hit is True, "deberia haber encontrado el ejercicio guardado y/o el eliminado"

    print()
    print(f"Enunciado guardado sembrado:   {saved_statement!r}")
    print(f"Enunciado eliminado sembrado:  {deleted_statement!r}")
    print(
        "OK (mecanico): memory_hit=true. Revisa a ojo los enunciados de arriba: "
        "ninguno deberia tratar el mismo tema que los dos sembrados (aunque usen otras palabras)."
    )


if __name__ == "__main__":
    asyncio.run(main())
