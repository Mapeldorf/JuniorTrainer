"""Herramienta `search_saved_exercises` del agente de ejercicios.

Requisito de `specs/agent-memory/spec.md`: un ejercicio no guardado o
eliminado nunca debe aparecer en el resultado. Conexion directa de solo
lectura con el rol `agents_exercise_reader` (ver app/db.py y
`infra/supabase/migrations/0003_agents_memory.sql`), hasta 3 consultas
por tarea, hasta 10 resultados cada una.

Decision de diseno (ver design.md "Contrato de entrada/salida del agente
de ejercicios"): la implementacion inicial hace una unica consulta por
tarea (filtrada por `exercise_type`), pero el budget se deja en 3 (el
techo que pide la spec) para que una futura consulta adicional (p. ej.
una por tecnologia relevante) no tenga que cambiar el contrato de
`SearchBudget`.
"""

from dataclasses import dataclass, field

import psycopg
from psycopg.rows import dict_row

from app.models import ExerciseCodeBlock


class SearchBudgetExceeded(RuntimeError):
    """Se intento una consulta por encima del limite de la tarea."""


class SearchBudget:
    """Cuenta las consultas hechas en una tarea A2A; agota a las 3 (por diseno)."""

    def __init__(self, max_calls: int = 3) -> None:
        self.max_calls = max_calls
        self.used = 0

    def consume(self) -> None:
        if self.used >= self.max_calls:
            raise SearchBudgetExceeded(
                f"se alcanzo el limite de {self.max_calls} consultas de esta tarea"
            )
        self.used += 1


@dataclass
class SavedExercise:
    statement: str
    code: list[ExerciseCodeBlock] = field(default_factory=list)
    expected_answer: str | None = None


_QUERY = """
    select statement, code, expected_answer
    from public.exercise
    where type = %(exercise_type)s
      and saved = true
      and deleted_at is null
    order by created_at desc
    limit %(limit)s
"""


async def search_saved_exercises(
    conn_string: str,
    exercise_type: str,
    budget: SearchBudget,
    limit: int = 10,
) -> list[SavedExercise]:
    """Consulta hasta `limit` ejercicios ya guardados del tipo pedido.

    Descuenta una consulta de `budget` ANTES de conectar, mismo criterio
    que `SearchBudget` del agente web: un budget agotado no hace ninguna
    llamada de mas aunque la conexion falle despues.
    """
    budget.consume()
    async with await psycopg.AsyncConnection.connect(conn_string, row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute(_QUERY, {"exercise_type": exercise_type, "limit": limit})
            rows = await cur.fetchall()
    return [
        SavedExercise(
            statement=row["statement"],
            code=_parse_code(row["code"]),
            expected_answer=row["expected_answer"],
        )
        for row in rows
    ]


def _parse_code(raw: object) -> list[ExerciseCodeBlock]:
    """`exercise.code` es jsonb y psycopg lo devuelve ya como list/dict de
    Python; se tolera cualquier forma inesperada devolviendo una lista
    vacia en vez de lanzar (este tool nunca deberia tumbar la tarea por un
    dato historico con una forma distinta a la que este agente escribe)."""
    if not isinstance(raw, list):
        return []
    blocks = []
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("code"), str):
            blocks.append(ExerciseCodeBlock(file=item.get("file"), code=item["code"]))
    return blocks
