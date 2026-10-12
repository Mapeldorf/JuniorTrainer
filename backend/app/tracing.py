"""Trazas de Langfuse de la orquestacion (tarea 6.7).

Mismo contrato que `agents/*/app/tracing.py` (ver esos ficheros para la
explicacion completa): `init_client()` construye el singleton de Langfuse
una sola vez por proceso con las credenciales de `Settings`, `new_trace_id()`
genera un id nuevo por generacion (no necesita el cliente inicializado --
`Langfuse.create_trace_id()` es un metodo estatico que solo formatea un id
aleatorio, confirmado inspeccionando el SDK antes de usarlo asi: no hace
red ni valida credenciales), y `record_generation()` abre un span
"orquestacion" bajo esa traza para que quede un nodo de nivel generacion,
ademas de los tres spans "agente-web"/"agente-code"/"agente-exercises" que
cada agente ya escribe bajo el mismo trace_id."""

import logging
from functools import lru_cache

from langfuse import Langfuse, get_client

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def init_client() -> None:
    settings = get_settings()
    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_base_url,
    )


def new_trace_id() -> str:
    return Langfuse.create_trace_id()


def record_generation(
    trace_id: str,
    generation_id: str,
    *,
    kind: str,
    technologies: list[str],
    has_repo: bool,
    status: str,
    error_message: str | None = None,
) -> None:
    """Marca en Langfuse que esta generacion (`trace_id`) ha terminado, con
    su resultado final. Un fallo aqui se registra y se ignora: la
    generacion ya ha terminado de verdad en Supabase, independientemente
    de si esto consigue escribirse en Langfuse."""
    try:
        init_client()
        client = get_client()
        with client.start_as_current_observation(
            name="orquestacion",
            as_type="span",
            trace_context={"trace_id": trace_id},
            input={"generation_id": generation_id, "kind": kind, "technologies": technologies, "has_repo": has_repo},
            output={"status": status, "error_message": error_message},
            metadata={"status": status},
        ):
            pass
        client.flush()
    except Exception:
        logger.warning(
            "fallo marcando el resultado de la generacion en Langfuse (trace_id=%s)",
            trace_id,
            exc_info=True,
        )


def record_answer_evaluation(
    trace_id: str,
    assignment_id: str,
    exercise_id: str,
    *,
    status: str,
    verdict: str | None = None,
    error_message: str | None = None,
) -> None:
    """Marca en Langfuse que esta evaluacion de respuesta (`trace_id`,
    grupo 5 del change `valoracion-respuestas`) ha terminado, con su
    resultado final. Analoga a `record_generation`; un fallo aqui se
    registra y se ignora: la respuesta ya ha terminado de evaluarse de
    verdad (o de fallar), independientemente de si esto consigue
    escribirse en Langfuse."""
    try:
        init_client()
        client = get_client()
        with client.start_as_current_observation(
            name="orquestacion-respuesta",
            as_type="span",
            trace_context={"trace_id": trace_id},
            input={"assignment_id": assignment_id, "exercise_id": exercise_id},
            output={"status": status, "verdict": verdict, "error_message": error_message},
            metadata={"status": status},
        ):
            pass
        client.flush()
    except Exception:
        logger.warning(
            "fallo marcando el resultado de la evaluacion en Langfuse (trace_id=%s)",
            trace_id,
            exc_info=True,
        )
