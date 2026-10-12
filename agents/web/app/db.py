"""Cadena de conexion directa a Postgres, compartida por memoria larga
(`app/memory.py`, `AsyncPostgresStore`) y memoria corta
(`app/checkpoint.py`, `AsyncPostgresSaver`).

Ambas usan el rol `agents_memory` (solo esquema `memory`, ver
`infra/supabase/migrations/0003_agents_memory.sql`), asi que la cadena de
conexion es identica para las dos; vivia duplicada en `memory.py` antes de
que existiera `checkpoint.py`.
"""

from app.config import get_settings


def conn_string() -> str:
    settings = get_settings()
    user = f"agents_memory.{settings.supabase_project_ref}"
    return (
        f"postgresql://{user}:{settings.agents_memory_password}"
        f"@{settings.agents_pg_host}:{settings.agents_pg_port}"
        f"/{settings.agents_pg_database}?sslmode=require"
    )
