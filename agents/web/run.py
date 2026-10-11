"""Punto de entrada para arrancar este servicio en LOCAL (sin
docker-compose). Usa `python run.py`, NO `uvicorn app.main:app`
directamente.

Hallazgo verificando la tarea 6.7 en Windows: `uvicorn app.main:app` (la
CLI) crea su loop (`asyncio.run()` dentro de `Server.run()`) y SOLO
DESPUES importa `app.main` -- la importacion ocurre dentro de la propia
corutina que ese loop ya esta ejecutando. Confirmado instrumentando
`asyncio.get_running_loop()` en `app/__init__.py`: para cuando ese
modulo se importa, ya hay un loop corriendo. El fix de Windows de
`app/__init__.py` (fijar `WindowsSelectorEventLoopPolicy`, necesario
para que psycopg en modo async no falle con
`Psycopg cannot use the 'ProactorEventLoop'...`) llega entonces
DEMASIADO TARDE: la politica se fija, pero el loop que ya existe (creado
bajo la politica anterior, `WindowsProactorEventLoopPolicy` por defecto)
no cambia retroactivamente.

Aqui se importa `app` ANTES de llamar a `uvicorn.run()`, mientras
todavia no hay ningun loop corriendo, para que la politica quede fijada
a tiempo. Sin efecto en Linux/macOS (incluida produccion, Docker): la
condicion del fix solo se cumple en Windows, y `python run.py` arranca
el mismo `app.main:app` que `uvicorn app.main:app` arrancaria, solo que
en el orden correcto.
"""

import app  # noqa: F401 -- el import en si es el fix (ver docstring); no quitarlo aunque parezca no usarse

import uvicorn

from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.agent_web_host, port=settings.agent_web_port)
