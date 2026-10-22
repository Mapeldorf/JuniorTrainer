"""Cadena de conexion directa a Postgres de este agente.

El agente de ejercicios usa el rol de solo lectura `agents_exercise_reader`
sobre `public.exercise` (`app/tools/saved_exercises.py`), ver design.md
"Contrato de entrada/salida del agente de ejercicios" e
`infra/supabase/migrations/0003_agents_memory.sql`.

Change `eliminar-memoria-agente-ejercicios`: este agente ya no usa el rol
`agents_memory` (tenia una conexion aparte aqui, `conn_string()`, para su
memoria propia en el esquema `memory`); ese rol sigue existiendo para los
agentes web y de codigo, que mantienen su propia copia de este modulo.
"""

from app.config import get_settings


def exercise_reader_conn_string() -> str:
    """Rol `agents_exercise_reader` (solo SELECT sobre `public.exercise`)."""
    settings = get_settings()
    user = f"agents_exercise_reader.{settings.supabase_project_ref}"
    return (
        f"postgresql://{user}:{settings.agents_exercise_reader_password}"
        f"@{settings.agents_pg_host}:{settings.agents_pg_port}"
        f"/{settings.agents_pg_database}?sslmode=require"
    )
