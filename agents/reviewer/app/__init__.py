"""Paquete de la app del agente revisor.

Fix de compatibilidad Windows (mismo que `agents/exercises/app/__init__.py`,
ver su docstring para la explicacion completa). No tiene coste en
Linux/produccion."""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
