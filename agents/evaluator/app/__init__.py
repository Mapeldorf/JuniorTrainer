"""Paquete de la app del agente evaluador.

Fix de compatibilidad Windows (mismo que `agents/exercises/app/__init__.py`,
ver su docstring para la explicacion completa): por defecto, Python usa
ProactorEventLoop como event loop de asyncio en Windows; este agente no
usa psycopg async (no tiene memoria propia), pero se mantiene el mismo
fix por consistencia con el resto de agentes y porque no tiene coste
alguno en Linux/produccion."""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
