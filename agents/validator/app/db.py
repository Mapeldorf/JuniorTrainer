"""Cadena de conexion directa a Postgres del rol de solo lectura de este
agente.

Mismo patron que `agents/exercises/app/db.py`: un unico rol con un unico
proposito (ver design.md "D2/D3" del change `validador-duplicados-tecnologias`
e `infra/supabase/migrations/0010_agents_validator_reader.sql`):
`agents_validator_reader` solo tiene `SELECT` sobre `public.technology`, nada
sobre el esquema `memory` ni sobre ninguna otra tabla.
"""

from app.config import get_settings


def conn_string() -> str:
    """Rol `agents_validator_reader` (solo `SELECT` sobre `public.technology`)."""
    settings = get_settings()
    user = f"agents_validator_reader.{settings.supabase_project_ref}"
    return (
        f"postgresql://{user}:{settings.agents_validator_reader_password}"
        f"@{settings.agents_pg_host}:{settings.agents_pg_port}"
        f"/{settings.agents_pg_database}?sslmode=require"
    )
