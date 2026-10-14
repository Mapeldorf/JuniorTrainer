# Tasks

## 1. Postgres dedicado para LiteLLM

- [x] 1.1 En `docker-compose.yml`, añadir el servicio `litellm-db` (imagen `postgres:16-alpine`, variables `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` desde `.env`, volumen nombrado `litellm-db-data` para persistencia, sin puerto publicado al host). Verificar que `docker compose config` resuelve el servicio sin errores.
- [x] 1.2 Añadir `LITELLM_DB_USER`, `LITELLM_DB_PASSWORD`, `LITELLM_DB_NAME` a `.env.example` (con nota de generar la password con `openssl rand -hex 32`, mismo estilo que `AGENTS_MEMORY_PASSWORD`).
- [x] 1.3 En `docker-compose.yml`, el servicio `litellm` añade `depends_on: litellm-db` y una variable `DATABASE_URL` construida a partir de `LITELLM_DB_*` apuntando a `litellm-db:5432`.

## 2. Configuracion de LiteLLM

- [x] 2.1 En `infra/litellm/config.yaml`, añadir `general_settings.master_key: os.environ/LITELLM_MASTER_KEY` y `general_settings.database_url: os.environ/DATABASE_URL`.
- [x] 2.2 Levantar `litellm` y `litellm-db` con `docker compose up litellm-db litellm` y verificar en los logs que LiteLLM aplica sus migraciones Prisma sin error y queda escuchando en el puerto 4000. Verificado ("All migrations have been successfully applied", "Uvicorn running on http://0.0.0.0:4000"); fue necesario primero eliminar un volumen `litellm-db-data` obsoleto de un intento anterior con otra password (ver conversacion).

## 3. Script de aprovisionamiento de virtual keys

- [x] 3.1 Crear `infra/litellm/provision_keys.py`: para cada uno de los 5 agentes (alias `agent-web`, `agent-code`, `agent-exercises`, `agent-evaluator`, `agent-reviewer`), consulta `GET /key/info` por alias contra el proxy local; si no existe, crea la key con `POST /key/generate` (autenticado con `LITELLM_MASTER_KEY`), restringida via `models` al modelo logico que le corresponde (`generator` para web/code/exercises, `evaluator` para evaluator, `reviewer` para reviewer); imprime por stdout el nombre de variable de entorno y el valor de cada key generada (o un aviso de "ya existe, omitida" si procede).
- [x] 3.2 Documentar en un comentario al inicio del script el comando de uso (`python infra/litellm/provision_keys.py`, variables de entorno que necesita: `LITELLM_MASTER_KEY`, URL del proxy).
- [x] 3.3 Ejecutar el script contra el `litellm` levantado en la tarea 2.2 y verificar que imprime 5 keys nuevas (formato `sk-...`), y que una segunda ejecucion inmediata las reporta como ya existentes sin generar keys nuevas (verifica la idempotencia por alias). Verificado; en el camino se corrigio el script: `/key/info` no admite buscar por `key_alias` (exige el valor real de la key), se cambio a `/key/list?key_alias=` que si soporta ese filtro.

## 4. Migrar los 5 agentes a su virtual key propia

- [x] 4.1 En `agents/web/app/config.py`, sustituir el campo `litellm_master_key: str` por `litellm_key: str`, leido de la variable `AGENT_WEB_LITELLM_KEY`; actualizar `agents/web/app/llm.py` para usar `settings.litellm_key` en `api_key`. Repetir el mismo cambio en `agents/code`, `agents/exercises` (variable `AGENT_CODE_LITELLM_KEY`, `AGENT_EXERCISES_LITELLM_KEY`), con `agent_evaluator`/`agent_reviewer` tomando `AGENT_EVALUATOR_LITELLM_KEY`/`AGENT_REVIEWER_LITELLM_KEY` respectivamente. Verificar en cada agente que `python -c "from app.config import get_settings"` no falla por el nuevo nombre de campo (con la variable de entorno correspondiente presente). Implementado con el nombre de campo `agent_<nombre>_litellm_key` (no `litellm_key` a secas) para seguir la convencion ya existente del proyecto (`agent_web_host`, `agent_service_token`, etc.: pydantic-settings mapea el nombre de campo al de la variable de entorno en mayusculas). Verificado en los 5 agentes.
- [x] 4.2 Añadir las 5 variables (`AGENT_WEB_LITELLM_KEY`, `AGENT_CODE_LITELLM_KEY`, `AGENT_EXERCISES_LITELLM_KEY`, `AGENT_EVALUATOR_LITELLM_KEY`, `AGENT_REVIEWER_LITELLM_KEY`) a `.env.example`, con las keys generadas en la tarea 3.3 pegadas en el `.env` local de desarrollo (no en `.env.example`, que queda vacio). Reducir el comentario de `LITELLM_MASTER_KEY` en `.env.example` para reflejar que ya es solo para administracion/aprovisionamiento, no para las llamadas de negocio de los agentes.

## 5. Verificacion end-to-end

- [x] 5.1 Con las 5 variables nuevas rellenas en `.env`, levantar `docker compose up` completo y verificar (p. ej. disparando una generacion de ejercicios desde el backend, o los scripts `verify_*.py` que ya existen en cada agente) que los 5 agentes siguen llamando a LiteLLM con normalidad usando su propia key. Verificado: los 5 agentes arrancan sin error con su config nueva, y una llamada real `/chat/completions` con cada una de las 5 virtual keys contra su modelo logico permitido responde 200 (llamada real al proveedor via LiteLLM).
- [x] 5.2 Verificar manualmente, con `curl` autenticado con la virtual key de `evaluator`, que una llamada al modelo `generator` es rechazada por LiteLLM (confirma la restriccion de `models` por key, requirement "Una key no puede llamar a un modelo que no le corresponde"). Verificado: `403 key_model_access_denied`, sin invocar al proveedor.
- [x] 5.3 Verificar manualmente que revocar la virtual key de un agente (`POST /key/delete` o UI) no interrumpe las llamadas de los otros 4 agentes, y que el agente revocado recibe un error de autenticacion en su siguiente llamada (requirement de revocacion independiente). Verificado: revocada la key de `agent-web` (`401 token_not_found_in_db`), las otras 4 siguieron respondiendo `200` con normalidad. Se re-aprovisiono despues con `provision_keys.py` para dejar el entorno funcional.
