# Design

## Context

Ver `proposal.md` para la motivacion. Estado tecnico relevante:

- `infra/litellm/config.yaml` hoy solo tiene `model_list` (tres modelos logicos: `generator`, `evaluator`, `reviewer`) y `litellm_settings` (callbacks de Langfuse). No hay `general_settings`.
- `docker-compose.yml` no tiene ningun Postgres propio; el `litellm` service arranca con `env_file: .env` y el `config.yaml` montado como volumen de solo lectura. `LITELLM_MASTER_KEY` llega al contenedor via ese `.env` y LiteLLM la toma automaticamente como master key si esta presente en el entorno (comportamiento por defecto del proxy, sin que `config.yaml` tenga que declararla).
- Los 5 agentes (`agents/{web,code,exercises,evaluator,reviewer}/app/config.py` y `app/llm.py`) tienen el mismo patron: un campo `litellm_master_key: str` en `Settings`, leido por `pydantic-settings` desde el `.env` unico del repo, y usado como `api_key` del cliente `ChatOpenAI` de `langchain-openai` contra `http://litellm:4000/v1`.
- Decision ya tomada con el usuario (no se revisita aqui): Postgres dedicado para LiteLLM, no el de Supabase que ya reutilizan los agentes para memoria (`AGENTS_PG_*`). Aisla el almacen de credenciales/keys del resto de datos de la aplicacion.

## Goals / Non-Goals

**Goals:**
- Que cada agente tenga una virtual key propia, restringida a su modelo logico, y que revocar una no afecte a las demas.
- Que el aprovisionamiento de esas 5 keys sea reproducible (se puede volver a ejecutar en un entorno nuevo) sin depender de clicks manuales en una UI.
- Minimizar la superficie nueva: sin pipeline de secrets management, sin orquestacion adicional mas alla de Docker Compose.

**Non-Goals:**
- No se implementan budgets (`max_budget`) en esta propuesta; es la siguiente pieza de la serie, y depende de que las virtual keys ya existan (un budget sin virtual key solo puede ser global, no por agente).
- No se expone la UI de administracion de LiteLLM (`/ui`) como parte de este cambio; el aprovisionamiento se hace via API con el script nuevo, no se decide aqui si exponer la UI en algun entorno.
- No se automatiza la rotacion periodica de las virtual keys; el mecanismo de revocacion/regeneracion queda disponible (requirement de la spec), pero activarlo on-demand es un procedimiento manual, no un cron.

## Decisions

- **Aprovisionamiento via script de un solo uso (`infra/litellm/provision_keys.py`) contra `/key/generate`, no vía UI ni vía definicion estatica en `config.yaml`.** LiteLLM no permite declarar virtual keys con restriccion de `models` de forma estatica en `config.yaml` sin DB (eso es lo que resuelve justamente el `general_settings.database_url` que esta propuesta añade): las virtual keys son filas gestionadas por LiteLLM en sus propias tablas, creadas en caliente via su API REST (`POST /key/generate`, autenticado con la `master_key`) o su UI web. Para un proyecto de este tamaño, sin pipeline de secrets management, la opcion mas simple y auditable es un script Python de arranque unico (no un servicio que corre en cada `docker-compose up`): se ejecuta a mano una vez por entorno (local, y cada entorno nuevo que se levante), imprime las 5 keys generadas, y quien lo ejecuta las pega en su `.env`. Alternativas descartadas:
  - UI web de LiteLLM (`/ui`): requiere exponer un puerto adicional y clicks manuales no reproducibles ni documentables en el repo; descartada para mantener el aprovisionamiento como codigo versionado (el script) en vez de un procedimiento tribal.
  - Definicion declarativa en `config.yaml`: no existe ese mecanismo en LiteLLM para virtual keys con restriccion de modelo (si existiera, seria la opcion preferida por ser la mas simple; se revisaria esta decision si una version futura de LiteLLM lo soporta).
- **El script es idempotente por `key_alias`, no por ejecucion unica forzada.** Antes de crear una key para un agente, consulta `/key/info` por su alias (`agent-web`, `agent-code`, etc.); si ya existe, la deja intacta y no genera una nueva (evita invalidar en caliente un `.env` ya configurado si alguien re-ejecuta el script sin querer). Para rotar una key a proposito, el procedimiento es revocarla explicitamente primero (`/key/delete` o UI) y volver a correr el script.
- **`master_key` sigue en `general_settings.master_key`, igual que hoy via `LITELLM_MASTER_KEY` en el entorno, pero su unico uso pasa a ser administrativo**: autenticar el propio script de aprovisionamiento contra `/key/generate`/`/key/info`. ningun agente la usa ya para llamadas de negocio.
- **Postgres dedicado (`litellm-db`) con imagen oficial `postgres:16-alpine` y un volumen nombrado**, igual de simple que cualquier otro servicio de infraestructura en `docker-compose.yml`; LiteLLM aplica sus propias migraciones Prisma al arrancar contra `database_url`, no hace falta un script de migracion propio.

## Risks / Trade-offs

- [El script de aprovisionamiento es un paso manual mas al levantar un entorno nuevo (ejecutarlo y copiar 5 keys a `.env`), mas friccion que antes (una sola `LITELLM_MASTER_KEY` compartida)] → Mitigacion: es exactamente el mismo tipo de paso manual que ya exige `AGENTS_MEMORY_PASSWORD`/`AGENTS_EXERCISE_READER_PASSWORD` en `.env.example` (generar con `openssl rand -hex 32` antes de aplicar una migracion); se documenta en `.env.example` con el mismo estilo de comentario que ya usa el resto del fichero.
- [Un Postgres nuevo es un servicio con estado que hay que hacer backup/mantener, aunque sea pequeño] → Mitigacion: solo guarda metadatos de control (keys, budgets, logs de uso), no datos de negocio; perderlo en un entorno de desarrollo solo implica re-ejecutar el script de aprovisionamiento. En produccion, igual que cualquier volumen Docker, requeriria backup si se quisiera preservar historico de uso, pero eso es una decision de despliegue fuera de alcance de esta propuesta.
- [Si el script de aprovisionamiento no se ejecuta en un entorno nuevo antes de levantar los agentes, estos fallan al arrancar (variable de entorno `AGENT_*_LITELLM_KEY` requerida y vacia)] → Mitigacion: es el mismo patron de fallo explicito en arranque que ya tienen las credenciales de Supabase/GitHub App (campos `str` obligatorios en `Settings`, sin default); falla rapido y de forma clara en vez de silenciosamente.
- [**BREAKING**: cualquier `.env` existente deja de bastar para los agentes hasta rellenar las 5 variables nuevas] → Mitigacion: ya señalado en `proposal.md`; es un cambio de un proyecto en desarrollo activo (TFM), no un despliegue con usuarios reales que migrar.
