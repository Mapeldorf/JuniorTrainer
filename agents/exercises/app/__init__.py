"""Paquete de la app del agente de ejercicios.

Fix de compatibilidad Windows + psycopg async: por defecto, Python usa
ProactorEventLoop como event loop de asyncio en Windows, pero psycopg en
modo async (usado por la conexion de solo lectura de
app/tools/saved_exercises.py) exige un event loop basado en selector. Sin
esto, cualquier conexion a Postgres desde un script de verificacion en
Windows falla con:
    psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to
    run in async mode...

Se aplica aqui (y no en cada script), igual que en agents/web y
agents/code, porque este modulo se importa como efecto colateral de
cualquier `from app.X import ...`, asi que cualquier entrypoint (scripts/,
uvicorn, tests) queda cubierto sin boilerplate repetido. No tiene efecto
en Linux/macOS (incluida produccion, que corre en contenedores Docker
Linux): la condicion solo se cumple en Windows.
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
