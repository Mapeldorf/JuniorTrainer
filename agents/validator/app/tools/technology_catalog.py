"""Herramienta `list_catalog_technologies` del agente validador.

Lectura de solo `SELECT` con el rol `agents_validator_reader` (ver app/db.py
e `infra/supabase/migrations/0010_agents_validator_reader.sql`), una unica
consulta por tarea: trae el catalogo completo de tecnologias para que
`app/service.py` pueda pedirle al modelo que compare cada entrada contra el
catalogo y detecte duplicados semanticos (ver design.md "D1/D3" del change
`validador-duplicados-tecnologias`). El catalogo es una lista de nombres
pensada para mostrarse entera en un selector de formulario
(`specs/technology-catalog/spec.md`), no un dataset grande, asi que no hace
falta un presupuesto de llamadas como el del agente de ejercicios.
"""

import psycopg

from app.db import conn_string

_QUERY = "select name from public.technology order by name"


async def list_catalog_technologies() -> list[str]:
    """Devuelve los nombres canonicos de todo el catalogo de tecnologias."""
    async with await psycopg.AsyncConnection.connect(conn_string()) as conn:
        async with conn.cursor() as cur:
            await cur.execute(_QUERY)
            rows = await cur.fetchall()
    return [row[0] for row in rows]
