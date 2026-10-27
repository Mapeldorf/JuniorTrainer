# Design

## Context

Ver proposal.md (Why). Estado de partida:

- Los 6 agentes leen `LITELLM_BASE_URL` con `pydantic-settings` (`agents/*/app/config.py`), con valor por defecto `http://litellm:4000/v1`, y cargan el `.env` de la raiz por ruta absoluta. En el contenedor, ademas, `docker-compose.yml` lo inyecta por `env_file: .env`.
- El arnes `evals/` ejecuta el codigo de los agentes **en el host** (`evals/agent_runner.py` lee `settings.litellm_base_url`) y `evals/judge.py` lee `LITELLM_BASE_URL` del entorno. Desde el host, LiteLLM esta en `http://localhost:4000/v1` (puerto publicado). El job `evals-gate` del CI pasa `LITELLM_BASE_URL` como variable del proceso.
- El backend no usa `LITELLM_BASE_URL`: tiene `LITELLM_URL: http://litellm:4000` fijado ya en su bloque `environment:`. Es exactamente el patron que aqui falta en los agentes.
- `.env.example` no documenta `LITELLM_BASE_URL`; en el `.env` local la añadio el usuario para el arnes.

## Goals / Non-Goals

**Goals:**
- Que el valor del `.env` pensado para el host no pueda llegar a los agentes en contenedor.
- Que el arnes desde el host siga leyendo `LITELLM_BASE_URL` del `.env` o del entorno, sin cambios de uso.

**Non-Goals:**
- Separar el `.env` en uno por entorno o por servicio (riesgo 7 del capstone, otro change).
- Revisar otras variables compartidas: se comprobo que la unica con `localhost` en el `.env` local es `LITELLM_BASE_URL`; `FRONTEND_URL=http://localhost:4200` es correcta porque la usa el navegador.

## Decisions

### Decision 1: fijar la URL en el bloque `environment:` de cada agente

En Compose, `environment` tiene prioridad sobre `env_file`, y en `pydantic-settings` la variable de entorno real tiene prioridad sobre el fichero `.env`. Con `LITELLM_BASE_URL: http://litellm:4000/v1` en `environment:`, el contenedor recibe la URL interna aunque el `.env` diga otra cosa, y el host sigue leyendo el `.env`. Es el mismo patron que ya usan el backend (`LITELLM_URL`) y los tres agentes que hablan con Presidio (`PRESIDIO_*_API_BASE`): URLs internas fijas, que no son secretos, en el compose y no en el `.env`.

**Alternativas descartadas:**
- *Quitar `LITELLM_BASE_URL` del `.env` y pedirla al arnes en cada ejecucion.* Arregla el sintoma en un entorno, no la causa: cualquiera que vuelva a ponerla en el `.env` rompe los contenedores, y el fallo no da ningun error visible en el arranque.
- *Renombrar la variable del host (por ejemplo `EVALS_LITELLM_BASE_URL`).* Cambia el contrato del arnes, de `evals/judge.py` y del job `evals-gate`, y obliga a tocar el codigo de los seis agentes para que lean un nombre distinto segun donde corran. Mas superficie para el mismo resultado.
- *Un ancla YAML compartida (`x-agent-env`).* Seis lineas repetidas son mas legibles que un ancla mezclada con los bloques que ya tienen las URLs de Presidio, y el fichero no usa anclas hoy.

### Decision 2: documentar la variable como "solo host"

`.env.example` gana una entrada comentada para `LITELLM_BASE_URL` que dice para que sirve (arnes y scripts desde el host), que valor lleva y que los contenedores la ignoran. Asi el siguiente que la añada sabe que no rompe nada.

## Risks / Trade-offs

- [Un agente nuevo se añade al compose sin la linea] → Volveria el fallo para ese agente. Mitigacion: comentario junto a cada bloque citando este change; la verificacion de la tarea 3 lo comprueba en los seis.
- [Despliegue con un gestor de secretos que inyecte `LITELLM_BASE_URL`] → El bloque `environment:` del compose ganaria igualmente, que es lo deseado dentro de la red de Compose. Fuera de Compose (otra plataforma) habria que fijarla alli; queda anotado en el design, no requiere cambio hoy.

## Migration Plan

Recrear los seis agentes (`docker compose up -d --no-build agent-web agent-code agent-exercises agent-evaluator agent-reviewer agent-validator`). Sin migracion de datos. Rollback: revertir el commit y recrear.
