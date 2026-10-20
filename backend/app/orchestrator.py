"""Orquestacion de una generacion (grupo 6): llama a los agentes web,
codigo y ejercicios por A2A, y escribe el resultado en `public.generation`/
`public.exercise` via el cliente admin (`service_role`) -- el unico sitio
del sistema con ese cliente (ver design.md "Decisions": `service_role`
exclusivo de FastAPI).

Flujo (requisitos de `specs/exercise-generation/spec.md`):
  - 6.4 "Orquestacion en paralelo": validacion de tecnologias (agente
    validador) como primer paso obligatorio, despues web+codigo en paralelo
    si hay repo (solo web si no hay repo).
  - 6.5 "Manejo de fallos parciales": el validador rechaza o falla ->
    error; web falla con repo -> se degrada (sigue sin fuentes de
    internet); codigo falla, ejercicios falla, o web falla sin repo ->
    error con el mensaje de la causa.
  - 6.6 "Limites de tiempo": 2 min por tarea A2A (ya lo aplica
    `send_a2a_task`, ver app/a2a_client.py), 5 min por generacion completa
    (aplicado aqui, envolviendo TODO el flujo).
  - 6.7 "Trazabilidad unificada": un trace_id de Langfuse por generacion,
    propagado a las llamadas A2A (validador, web, codigo y ejercicios).

Change `validacion-tecnologias-agente-juez`: el agente validador decide si
las tecnologias son tecnologias de programacion antes de arrancar nada mas;
un rechazo o un fallo del validador marca la generacion en error sin
ejecutar ningun agente de entrada (fail-closed).
"""

import asyncio
import logging

from app.a2a_client import A2ATaskError, send_a2a_task
from app.config import get_settings
from app.github_client import CommitResolutionError, resolve_head_commit
from app.supabase_client import get_admin_client
from app.tracing import new_trace_id, record_generation

logger = logging.getLogger(__name__)

# Limite de la generacion completa (tarea 6.6). El limite por tarea A2A
# individual vive en app/a2a_client.py (DEFAULT_TASK_TIMEOUT_SECONDS).
GENERATION_TIMEOUT_SECONDS = 300.0


class _GenerationFailed(RuntimeError):
    """Fallo irrecuperable de la generacion (requisito "Error si falla una
    entrada imprescindible"). El mensaje es el que se guarda tal cual en
    `generation.error_message`."""


def _split_exercise_requests(kind: str, count: int) -> list[tuple[str, int]]:
    """Cuantas llamadas al agente de ejercicios hacer, y con que `count`
    cada una. El agente de ejercicios solo acepta un `exercise_type` por
    llamada (decision documentada en design.md, tarea 5.1-5.3: "un agente
    que solo sabe producir un tipo por llamada es mas simple"), asi que
    `kind='both'` se resuelve aqui pidiendo dos tandas.

    Reparto determinista: `knowledge` se lleva el techo de `count/2` y
    `debug` el resto, para que la suma siga siendo exactamente `count`
    (requisito "Numero de ejercicios candidatos": 1-5 POR GENERACION, no
    por tipo). Caso borde `count == 1` con `kind='both'`: no se puede
    pedir "de los dos tipos" con un solo candidato sin pasarse de 1 en
    total, asi que se resuelve como si solo se hubiera pedido `knowledge`
    -- mas simple que rechazar la combinacion, y "al menos un candidato
    del tipo por defecto" es una degradacion razonable de "ambos tipos"
    cuando no hay sitio para los dos."""
    if kind != "both":
        return [(kind, count)]
    if count == 1:
        return [("knowledge", 1)]
    knowledge_count = -(-count // 2)  # techo
    debug_count = count - knowledge_count
    return [("knowledge", knowledge_count), ("debug", debug_count)]


async def _call_validator(technologies: list[str], trace_id: str) -> None:
    """Puerta de validacion previa (change `validacion-tecnologias-agente-juez`):
    pide al agente validador que decida si las tecnologias son tecnologias de
    programacion. Un rechazo o un fallo del validador es fatal para la
    generacion (fail-closed): no se ejecuta ningun agente de entrada."""
    settings = get_settings()
    try:
        result = await send_a2a_task(
            settings.agent_validator_url,
            {"technologies": technologies, "context": "generation"},
            trace_id=trace_id,
        )
    except A2ATaskError as exc:
        raise _GenerationFailed(f"el agente validador ha fallado: {exc}") from exc

    if not result.get("valid"):
        reason = result.get("reason") or "la entrada no parece una tecnologia de programacion"
        invalid = result.get("invalid_technologies") or []
        detail = f"{reason} ({', '.join(str(t) for t in invalid)})" if invalid else reason
        raise _GenerationFailed(
            f"las tecnologias no parecen tecnologias de programacion: {detail}"
        )


async def _call_web(technologies: list[str], trace_id: str, *, required: bool) -> dict | None:
    settings = get_settings()
    try:
        return await send_a2a_task(settings.agent_web_url, {"technologies": technologies}, trace_id=trace_id)
    except A2ATaskError as exc:
        if required:
            raise _GenerationFailed(f"el agente web ha fallado: {exc}") from exc
        logger.warning(
            "el agente web ha fallado habiendo repositorio disponible; la generacion sigue sin fuentes de internet: %s",
            exc,
        )
        return None


async def _call_code(owner: str, repo: str, commit_sha: str, technologies: list[str], trace_id: str) -> dict:
    settings = get_settings()
    try:
        return await send_a2a_task(
            settings.agent_code_url,
            {"owner": owner, "repo": repo, "commit_sha": commit_sha, "technologies": technologies},
            trace_id=trace_id,
        )
    except A2ATaskError as exc:
        raise _GenerationFailed(f"el agente de codigo ha fallado: {exc}") from exc


async def _gather_inputs(
    technologies: list[str], owner: str | None, repo: str | None, commit_sha: str | None, trace_id: str
) -> tuple[dict | None, dict | None]:
    if not owner or not repo:
        web_result = await _call_web(technologies, trace_id, required=True)
        return web_result, None

    settings = get_settings()
    web_outcome, code_outcome = await asyncio.gather(
        send_a2a_task(settings.agent_web_url, {"technologies": technologies}, trace_id=trace_id),
        send_a2a_task(
            settings.agent_code_url,
            {"owner": owner, "repo": repo, "commit_sha": commit_sha, "technologies": technologies},
            trace_id=trace_id,
        ),
        return_exceptions=True,
    )
    # return_exceptions=True (no el comportamiento por defecto de gather):
    # asi SIEMPRE se espera a que ambas tareas terminen antes de decidir
    # nada, en vez de que gather devuelva el control en cuanto la primera
    # lanza y deje la otra corriendo de fondo sin que nadie la recoja.

    if isinstance(code_outcome, BaseException):
        if isinstance(code_outcome, A2ATaskError):
            raise _GenerationFailed(f"el agente de codigo ha fallado: {code_outcome}") from code_outcome
        raise code_outcome

    if isinstance(web_outcome, BaseException):
        if not isinstance(web_outcome, A2ATaskError):
            raise web_outcome
        logger.warning(
            "el agente web ha fallado habiendo repositorio disponible; la generacion sigue sin fuentes de internet: %s",
            web_outcome,
        )
        web_result = None
    else:
        web_result = web_outcome

    return web_result, code_outcome


async def _call_exercises(
    exercise_type: str, count: int, web_result: dict | None, code_result: dict | None, trace_id: str
) -> dict:
    settings = get_settings()
    try:
        return await send_a2a_task(
            settings.agent_exercises_url,
            {
                "exercise_type": exercise_type,
                "count": count,
                "web_result": web_result,
                "code_result": code_result,
            },
            trace_id=trace_id,
        )
    except A2ATaskError as exc:
        raise _GenerationFailed(f"el agente de ejercicios ha fallado: {exc}") from exc


async def _generate_candidates(
    kind: str, count: int, web_result: dict | None, code_result: dict | None, trace_id: str
) -> list[dict]:
    candidates: list[dict] = []
    for exercise_type, sub_count in _split_exercise_requests(kind, count):
        result = await _call_exercises(exercise_type, sub_count, web_result, code_result, trace_id)
        candidates.extend(result.get("candidates", []))
    return candidates


def _insert_candidates(generation_id: str, candidates: list[dict]) -> None:
    if not candidates:
        return
    rows = [
        {
            "generation_id": generation_id,
            "type": candidate["type"],
            "name": candidate["name"],
            "statement": candidate["statement"],
            "code": candidate.get("code", []),
            "expected_answer": candidate.get("expected_answer"),
        }
        for candidate in candidates
    ]
    get_admin_client().table("exercise").insert(rows).execute()


def _mark_status(generation_id: str, status: str, error_message: str | None = None) -> None:
    get_admin_client().table("generation").update(
        {"status": status, "error_message": error_message}
    ).eq("id", generation_id).execute()


def _write_repo_access_log(
    generation_id: str, tech_lead_id: str, owner: str, repo: str, commit_sha: str | None, result: str
) -> None:
    """Requisito "Registro de auditoria de cada acceso" de
    `specs/github-repo-access/spec.md`: una fila por cada intento de
    acceso a un repositorio, exito o fallo, escrita antes de pasar nada al
    agente de codigo."""
    get_admin_client().table("repo_access_log").insert(
        {
            "generation_id": generation_id,
            "tech_lead_id": tech_lead_id,
            "owner": owner,
            "repo": repo,
            "commit_sha": commit_sha,
            "result": result,
        }
    ).execute()


async def _resolve_commit(generation_id: str, tech_lead_id: str, owner: str, repo: str) -> str:
    """Resuelve y fija el commit HEAD de `owner/repo` (requisito "Commit
    fijado por generacion"), antes de llamar a ningun agente. Un fallo
    aqui (repo inexistente, App no instalada) es fatal para la generacion
    (tarea 3.4), pero igualmente queda registrado en la auditoria."""
    try:
        commit_sha = await resolve_head_commit(owner, repo)
    except CommitResolutionError as exc:
        _write_repo_access_log(generation_id, tech_lead_id, owner, repo, None, "error")
        raise _GenerationFailed(f"no se pudo acceder al repositorio {owner}/{repo}: {exc}") from exc
    _write_repo_access_log(generation_id, tech_lead_id, owner, repo, commit_sha, "ok")
    return commit_sha


async def _orchestrate(
    generation_id: str,
    technologies: list[str],
    owner: str | None,
    repo: str | None,
    tech_lead_id: str,
    kind: str,
    count: int,
    trace_id: str,
) -> None:
    # Primer paso obligatorio: validar que las tecnologias son tecnologias de
    # programacion. Si el validador rechaza o falla, no se ejecuta nada mas.
    await _call_validator(technologies, trace_id)

    commit_sha: str | None = None
    if owner and repo:
        commit_sha = await _resolve_commit(generation_id, tech_lead_id, owner, repo)

    web_result, code_result = await _gather_inputs(technologies, owner, repo, commit_sha, trace_id)
    candidates = await _generate_candidates(kind, count, web_result, code_result, trace_id)
    _insert_candidates(generation_id, candidates)
    _mark_status(generation_id, "ready")


async def run_generation(
    generation_id: str,
    technologies: list[str],
    owner: str | None,
    repo: str | None,
    kind: str,
    count: int,
    tech_lead_id: str,
) -> None:
    """Punto de entrada que lanza `BackgroundTasks` (tarea 6.2): corre
    despues de que la respuesta HTTP de `POST /generations` ya se ha
    enviado (requisito "Generacion no se ejecuta en la peticion HTTP")."""
    trace_id = new_trace_id()
    has_repo = bool(owner and repo)

    try:
        await asyncio.wait_for(
            _orchestrate(generation_id, technologies, owner, repo, tech_lead_id, kind, count, trace_id),
            timeout=GENERATION_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        message = f"la generacion ha superado el limite de {GENERATION_TIMEOUT_SECONDS:.0f} segundos"
        _mark_status(generation_id, "error", message)
        record_generation(
            trace_id, generation_id, kind=kind, technologies=technologies, has_repo=has_repo,
            status="error", error_message=message,
        )
        return
    except _GenerationFailed as exc:
        _mark_status(generation_id, "error", str(exc))
        record_generation(
            trace_id, generation_id, kind=kind, technologies=technologies, has_repo=has_repo,
            status="error", error_message=str(exc),
        )
        return
    except Exception as exc:  # fallo inesperado no cubierto por los casos de arriba
        logger.exception("fallo inesperado orquestando la generacion %s", generation_id)
        _mark_status(generation_id, "error", f"fallo inesperado: {exc}")
        record_generation(
            trace_id, generation_id, kind=kind, technologies=technologies, has_repo=has_repo,
            status="error", error_message=str(exc),
        )
        return

    record_generation(
        trace_id, generation_id, kind=kind, technologies=technologies, has_repo=has_repo, status="ready"
    )
