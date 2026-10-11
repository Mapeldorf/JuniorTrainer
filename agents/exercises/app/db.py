"""Cadenas de conexion directa a Postgres de este agente.

A diferencia de web/codigo (un solo rol, `agents_memory`), el agente de
ejercicios usa DOS roles con proposito distinto (ver design.md "Contrato
de entrada/salida del agente de ejercicios" e
`infra/supabase/migrations/0003_agents_memory.sql`):
  - `agents_memory`: memoria larga propia (`app/memory.py`), esquema `memory`.
  - `agents_exercise_reader`: solo lectura de `public.exercise`
    (`app/tools/saved_exercises.py`), nada de `memory`.

Credenciales y conexion separadas a proposito -- una fuga de una no debe
dar acceso a lo que cubre la otra.
"""

from app.config import get_settings


def conn_string() -> str:
    """Rol `agents_memory` (memoria larga, esquema `memory`)."""
    settings = get_settings()
    user = f"agents_memory.{settings.supabase_project_ref}"
    return (
        f"postgresql://{user}:{settings.agents_memory_password}"
        f"@{settings.agents_pg_host}:{settings.agents_pg_port}"
        f"/{settings.agents_pg_database}?sslmode=require"
    )


def exercise_reader_conn_string() -> str:
    """Rol `agents_exercise_reader` (solo SELECT sobre `public.exercise`)."""
    settings = get_settings()
    user = f"agents_exercise_reader.{settings.supabase_project_ref}"
    return (
        f"postgresql://{user}:{settings.agents_exercise_reader_password}"
        f"@{settings.agents_pg_host}:{settings.agents_pg_port}"
        f"/{settings.agents_pg_database}?sslmode=require"
    )
