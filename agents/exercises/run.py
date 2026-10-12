"""Punto de entrada para arrancar este servicio en LOCAL (sin
docker-compose). Usa `python run.py`, NO `uvicorn app.main:app`
directamente -- mismo motivo que `agents/web/run.py` (ver su docstring):
`uvicorn app.main:app` importa `app` DESDE DENTRO de su propio loop ya
corriendo, demasiado tarde para que el fix de Windows de
`app/__init__.py` tenga efecto sobre ese loop."""

import app  # noqa: F401 -- el import en si es el fix; no quitarlo aunque parezca no usarse

import uvicorn

from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.agent_exercises_host, port=settings.agent_exercises_port)
