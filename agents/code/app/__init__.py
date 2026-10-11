"""Paquete de la app del agente de codigo.

Fix de compatibilidad Windows + psycopg async: por defecto, Python usa
ProactorEventLoop como event loop de asyncio en Windows, pero psycopg en
modo async (usado por langgraph-checkpoint-postgres, memoria larga/corta
de este agente) exige un event loop basado en selector. Sin esto,
cualquier conexion a Postgres desde un script de verificacion en Windows
falla con:
    psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to
    run in async mode...

Mismo fix que `agents/web/app/__init__.py` (ver su commit 89c2d78), por la
misma razon: se aplica aqui para que cualquier entrypoint (scripts/,
uvicorn, tests) quede cubierto sin repetir el fix en cada fichero. Sin
efecto en Linux/macOS, incluida produccion.
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
