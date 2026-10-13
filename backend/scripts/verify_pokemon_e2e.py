"""Prueba de aceptacion de extremo a extremo (grupo 8, tareas 8.1-8.3 del
change `generacion-ejercicios-agentes`; adaptada por el change
`acceso-repo-github-tool`, grupo 5, para leer el repositorio via GitHub en
vez de un `repo_path` local): una generacion real con un repositorio real
de GitHub, contra toda la infraestructura real (LiteLLM/OpenRouter,
Tavily, Postgres de memoria, Langfuse, API de GitHub) orquestada por el
`docker-compose.yml` -- los tres agentes aqui son servicios A2A reales en
contenedores separados, no servidores sueltos como en `verify_generation_e2e.py`.

Se llama a `run_generation()` directamente, no a traves de `POST
/generations`: la tarea 8.1 pide lanzar y verificar la generacion en si,
no la capa HTTP/autenticacion (ya cubierta en 6.2/6.3). Se ejecuta DOS
veces con el mismo repo y las mismas tecnologias (8.1 la primera vez, 8.3
la repeticion), capturando sin tocar `orchestrator.py`:
  - el `trace_id` de cada generacion (igual que 6.7), para comprobar en
    Langfuse que las trazas de los tres agentes quedan agrupadas (8.2);
  - el resultado crudo (`dict`, con su `memory_hit`) de cada llamada A2A a
    los agentes web y codigo, para comprobar en la SEGUNDA generacion que
    ambos devuelven `memory_hit=True` (8.3: no repiten busqueda ni relectura).
No hay una aserción automatica de "no repite el tema" del agente de
ejercicios (8.3): es un requisito semantico, no estructural. El script
imprime los enunciados de las dos tandas uno al lado del otro para
revisarlo a ojo (y queda tambien visible en Langfuse, en el input del
agente de ejercicios, que lista los enunciados previos que no debia repetir).

Tarea 5.3 (`acceso-repo-github-tool`): tambien comprueba que
`repo_access_log` tiene una fila con `result='ok'` y un `commit_sha` no
vacio para cada una de las dos generaciones.

Preparacion:
  1. Crea una GitHub App de solo lectura (`contents: read`) e instalala en
     el repositorio de prueba (ver README.md, seccion "GitHub App").
  2. .env real en la raiz del repo (Supabase, LiteLLM/OpenRouter, Tavily,
     Postgres de memoria, Langfuse, GITHUB_APP_ID/GITHUB_APP_PRIVATE_KEY)
     -- el mismo que usa `docker-compose.yml`.
  3. Levanta toda la pila:
         docker compose up -d --build
  4. Ya debe existir un profile con role='tech_lead' (si no,
     `docker compose exec backend python -m scripts.seed_tech_lead ...`).

Uso (desde la raiz del repo, con todo levantado):
    docker compose exec backend python -m scripts.verify_pokemon_e2e \
        --owner <owner> --repo <repo> --technologies "Python,Flask" \
        [--kind both] [--count 3]

`--technologies` son las tecnologias reales que usa ese repo, separadas
por comas.
"""

import argparse
import asyncio

import app.a2a_client as a2a_client
import app.orchestrator as orchestrator
import app.tracing as tracing
from app.config import get_settings
from app.supabase_client import get_admin_client

_original_new_trace_id = tracing.new_trace_id
_original_send_a2a_task = a2a_client.send_a2a_task
_captured_trace_id: dict = {}
_captured_calls: list[dict] = []


def _capturing_new_trace_id() -> str:
    trace_id = _original_new_trace_id()
    _captured_trace_id["trace_id"] = trace_id
    return trace_id


async def _capturing_send_a2a_task(url, data, **kwargs):
    result = await _original_send_a2a_task(url, data, **kwargs)
    _captured_calls.append({"url": url, "data": data, "result": result})
    return result


# Mismo motivo que en verify_generation_e2e.py (tarea 6.7): orchestrator.py
# importa ambos nombres directamente (`from app.tracing import new_trace_id`,
# `from app.a2a_client import send_a2a_task`), asi que hay que parchear la
# referencia que usa el propio modulo, no el modulo original.
orchestrator.new_trace_id = _capturing_new_trace_id
orchestrator.send_a2a_task = _capturing_send_a2a_task


def _memory_hit_for(url: str) -> bool | None:
    for call in _captured_calls:
        if call["url"] == url:
            return call["result"].get("memory_hit")
    return None


def _repo_access_log_row(admin, generation_id: str) -> dict | None:
    rows = (
        admin.table("repo_access_log")
        .select("owner, repo, commit_sha, result")
        .eq("generation_id", generation_id)
        .execute()
        .data
    )
    return rows[0] if rows else None


async def _run_one_generation(
    admin, tech_lead_id: str, owner: str, repo: str, technologies: list[str], kind: str, count: int
) -> dict:
    _captured_calls.clear()
    _captured_trace_id.clear()

    result = (
        admin.table("generation")
        .insert(
            {
                "repo_name": f"{owner}/{repo}",
                "technologies": ", ".join(technologies),
                "kind": kind,
                "status": "generating",
                "created_by": tech_lead_id,
            }
        )
        .execute()
    )
    generation_id = result.data[0]["id"]

    await orchestrator.run_generation(generation_id, technologies, owner, repo, kind, count, tech_lead_id)

    row = (
        admin.table("generation")
        .select("status, error_message")
        .eq("id", generation_id)
        .limit(1)
        .execute()
        .data[0]
    )
    if row["status"] != "ready":
        raise SystemExit(f"la generacion {generation_id} no quedo en 'ready': {row}")

    candidates = (
        admin.table("exercise")
        .select("id, type, statement")
        .eq("generation_id", generation_id)
        .execute()
        .data
    )
    if not (1 <= len(candidates) <= 5):
        raise SystemExit(f"se esperaban entre 1 y 5 candidatos, llegaron {len(candidates)}: {candidates}")

    access_log_row = _repo_access_log_row(admin, generation_id)
    if access_log_row is None:
        raise SystemExit(f"no se encontro ninguna fila en repo_access_log para la generacion {generation_id}")
    if access_log_row["result"] != "ok" or not access_log_row["commit_sha"]:
        raise SystemExit(f"repo_access_log de {generation_id} no es el esperado: {access_log_row}")

    settings = get_settings()
    return {
        "generation_id": generation_id,
        "trace_id": _captured_trace_id.get("trace_id"),
        "candidates": candidates,
        "web_memory_hit": _memory_hit_for(settings.agent_web_url),
        "code_memory_hit": _memory_hit_for(settings.agent_code_url),
        "repo_access_log": access_log_row,
    }


def _print_summary(label: str, summary: dict) -> None:
    print(f"\n--- {label} ---")
    print(f"generation_id: {summary['generation_id']}")
    print(f"trace_id: {summary['trace_id']}")
    if summary["trace_id"]:
        from langfuse import get_client

        tracing.init_client()
        print(f"Langfuse URL: {get_client().get_trace_url(trace_id=summary['trace_id'])}")
    print(f"web memory_hit: {summary['web_memory_hit']}")
    print(f"code memory_hit: {summary['code_memory_hit']}")
    print(f"repo_access_log: {summary['repo_access_log']}")
    print(f"candidatos ({len(summary['candidates'])}):")
    for candidate in summary["candidates"]:
        print(f"  [{candidate['type']}] {candidate['statement'][:120]}")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True, help="Propietario del repositorio de GitHub")
    parser.add_argument("--repo", required=True, help="Nombre del repositorio de GitHub")
    parser.add_argument("--technologies", required=True, help="Lista separada por comas")
    parser.add_argument("--kind", default="both", choices=["knowledge", "debug", "both"])
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()

    technologies = [t.strip() for t in args.technologies.split(",") if t.strip()]
    if not technologies:
        raise SystemExit("--technologies no puede quedar vacio")

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
    print(f"owner/repo: {args.owner}/{args.repo}")
    print(f"technologies: {technologies}")
    print(f"kind={args.kind} count={args.count}")

    first = await _run_one_generation(admin, tech_lead_id, args.owner, args.repo, technologies, args.kind, args.count)
    _print_summary("1a generacion (8.1)", first)

    second = await _run_one_generation(admin, tech_lead_id, args.owner, args.repo, technologies, args.kind, args.count)
    _print_summary("2a generacion, mismo repo y tecnologias (8.3)", second)

    print("\n--- comprobaciones automaticas (8.3 + 5.3 de acceso-repo-github-tool) ---")
    ok = True
    if second["web_memory_hit"] is not True:
        print(f"FALLO: se esperaba web_memory_hit=True en la 2a generacion, fue {second['web_memory_hit']}")
        ok = False
    else:
        print("OK: agente web no ha repetido tavily_search (memory_hit=True)")
    if second["code_memory_hit"] is not True:
        print(f"FALLO: se esperaba code_memory_hit=True en la 2a generacion, fue {second['code_memory_hit']}")
        ok = False
    else:
        print("OK: agente de codigo no ha reledo el repo (memory_hit=True)")
    if first["repo_access_log"]["commit_sha"] != second["repo_access_log"]["commit_sha"]:
        print(
            "FALLO: el commit_sha de repo_access_log deberia ser el mismo en ambas "
            f"generaciones (mismo repo): {first['repo_access_log']} vs {second['repo_access_log']}"
        )
        ok = False
    else:
        print(f"OK: repo_access_log registrado con result='ok' y commit_sha={first['repo_access_log']['commit_sha']!r} en ambas generaciones")

    print(
        "\nRevision manual pendiente (8.3, requisito semantico -- compara los enunciados de arriba): "
        "el agente de ejercicios no debe repetir el TEMA de un enunciado ya propuesto en la 1a tanda."
    )
    print(
        "Revision manual pendiente (8.2): en Langfuse, busca cada trace_id de arriba y comprueba que "
        "'orquestacion' (backend), 'agente-web', 'agente-code' y 'agente-exercises' aparecen agrupados bajo el."
    )

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
