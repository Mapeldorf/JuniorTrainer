"""Cadena de conexion directa a Postgres para la memoria larga del agente
web (`app/memory.py`, `AsyncPostgresStore`).

Usa el rol `agents_memory` (solo esquema `memory`, ver
`infra/supabase/migrations/0003_agents_memory.sql`).
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
