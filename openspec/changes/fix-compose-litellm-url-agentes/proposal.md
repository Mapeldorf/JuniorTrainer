# Proposal

## Why

Detectado al hacer capturas de la aplicacion en local (26 y 27 de octubre de 2026): el agente validador respondia "El validador no esta disponible en este momento" y el log del contenedor mostraba `openai.APIConnectionError: Connection error.` en cada llamada al modelo. Causa raiz confirmada con `docker exec juniortrainer-agent-validator-1 sh -c 'echo $LITELLM_BASE_URL'`: el `.env` de la raiz tenia `LITELLM_BASE_URL=http://localhost:4000/v1`, el valor que necesita el arnes de evaluacion cuando corre desde el host, y `docker-compose.yml` pasa ese `.env` a los 6 agentes por `env_file`. Dentro de un contenedor, `localhost` es el propio agente, asi que ninguno llega a LiteLLM. El valor por defecto del codigo (`agents/*/app/config.py`: `http://litellm:4000/v1`) es correcto, pero el `.env` lo pisa.

Es el mismo tipo de fallo que `fix-agent-model-env-collision`: una variable que comparten host y contenedores a traves de un unico `.env`, y que en uno de los dos lados tiene el valor equivocado. Mientras el `.env` lleve esa variable, **recrear el stack deja a los seis agentes sin acceso a ningun modelo**: se comprobo tras recrearlo el 27 de octubre (los seis volvieron a `http://localhost:4000/v1`).

## What Changes

- `docker-compose.yml`: fijar `LITELLM_BASE_URL: http://litellm:4000/v1` en el bloque `environment:` de `agent-web`, `agent-code`, `agent-exercises`, `agent-evaluator`, `agent-reviewer` y `agent-validator`. En Compose, `environment` tiene prioridad sobre `env_file`, asi que el contenedor recibe siempre la URL interna, lleve el `.env` lo que lleve.
- `.env.example`: documentar `LITELLM_BASE_URL` como variable **solo para el host** (arnes `evals/`, scripts de verificacion), que los contenedores ignoran.
- `evals/README.md`: decir que el modo real desde el host necesita `LITELLM_BASE_URL` apuntando a `localhost`, y que ponerla en el `.env` ya no rompe los contenedores.
- Sin cambios en el codigo de los agentes: su valor por defecto ya es el correcto.

## Capabilities

### New Capabilities
<!-- ninguna -->

### Modified Capabilities
- `litellm-agent-keys`: añade un requirement explicito de que los agentes en contenedor llegan al proxy por su URL interna, sin depender de ningun valor de `LITELLM_BASE_URL` pensado para el host. La spec ya garantizaba que cada agente envia su alias logico correcto (`fix-agent-model-env-collision`), pero no que la llamada llegue al proxy.

## Impact

- `docker-compose.yml`: seis bloques `environment:` (tres de ellos se crean; los otros tres ya existen por las URLs de Presidio).
- `.env.example` y `evals/README.md`: documentacion.
- Sin cambios en `agents/*`, `backend/`, `infra/litellm/` ni el CI: el job `evals-gate` ya pasa `LITELLM_BASE_URL` como variable de entorno del proceso del host.
- Corrige un fallo de disponibilidad reproducible: con el `.env` actual del entorno local, recrear el stack deja la aplicacion sin poder validar, generar ni valorar.
