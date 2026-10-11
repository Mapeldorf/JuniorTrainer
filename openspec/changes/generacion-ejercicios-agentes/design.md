# Design

## Context

Ver `proposal.md` - Why. Estado actual: el esquema de Supabase ya tiene `generation` (con `status` en `generating`/`ready`/`done`/`error`) y `exercise` (con `saved`/`deleted_at`) aplicados y sin usar todavia — nadie los escribe. El backend FastAPI solo tiene auth (`esqueleto-monorepo-auth`). `docker-compose.yml` solo trae `frontend`, `backend` y `litellm`; `litellm` ya expone el modelo logico `generator` resuelto por variables de entorno (seccion 11 de la especificacion), que el usuario ya ha configurado con OpenRouter.

## Goals / Non-Goals

**Goals:**
- Que los tres agentes de generacion corran como servicios A2A reales, orquestados por FastAPI, con memoria persistente y trazas en Langfuse.
- Reutilizar `generation`/`exercise` tal como estan; no son necesarios cambios de esquema en `public`.
- Mantener `service_role` exclusivo de FastAPI (seccion 11 de la especificacion): el agente de ejercicios NO debe usarlo para consultar `exercise`.

**Non-Goals:**
- Guardar ejercicios candidatos como definitivos, bloques, asignaciones, evaluador/revisor (paso 3).
- Cualquier pantalla de frontend para lanzar o ver una generacion.
- Preparacion/subida del repositorio en si (clonado, extraccion de zip): se asume que, al llegar al orquestador, el repo ya esta en una carpeta local legible; como se prepara esa carpeta es un detalle de implementacion de las tareas, no un requisito de spec nuevo.

## Decisions

**Los tres agentes son procesos Python separados (`agents/web/`, `agents/code/`, `agents/exercises/`), cada uno su propio servicio A2A con `a2a-sdk`.** Alternativa considerada: un unico proceso que sirva los tres "agentes" como rutas distintas. Se descarta porque la especificacion (seccion 7) los define como servicios A2A independientes con su propia Agent Card — mezclarlos en un proceso rompe el aislamiento de fallos que pide la seccion 7 (que falle el de codigo no debe poder tumbar al web) y complica los limites de tiempo por tarea.

**Los agentes llaman al modelo `generator` via el proxy HTTP de LiteLLM ya existente (`http://litellm:4000`), con un cliente OpenAI-compatible (`langchain-openai`), autenticados con `LITELLM_MASTER_KEY`.** Alternativa considerada: que cada agente use el SDK de `litellm` directamente con `GENERATOR_MODEL`/`GENERATOR_API_KEY` propios. Se descarta: duplicaria en cada agente la resolucion de proveedor que `infra/litellm/config.yaml` ya centraliza, y expondria la clave real de OpenRouter en tres contenedores en vez de uno. Con el proxy, los agentes solo necesitan la URL interna del servicio y la master key.

**Memoria en un esquema `memory` nuevo de PostgreSQL, con conexion directa (no via PostgREST/`service_role`), usando un rol `agents_memory` de solo ese esquema.** `langgraph-checkpoint-postgres` (`PostgresSaver`+`PostgresStore`) exige una conexion Postgres nativa; no hay forma de usarlo a traves de la API REST de Supabase. El rol `agents_memory` SHALL tener `USAGE`+`CREATE` solo sobre `memory`, nada sobre `public`, para que una fuga de sus credenciales no exponga datos de alumnos ni ejercicios.

**`search_saved_exercises` usa un segundo rol de Postgres, `agents_exercise_reader`, con `SELECT` solo sobre `public.exercise`, en conexion directa — no `service_role`.** La especificacion original reserva `service_role` para FastAPI (seccion 11); darselo al agente de ejercicios lo convertiria en un segundo punto con acceso total a la base de datos. Un rol de solo lectura sobre una sola tabla es coherente con el principio de RLS como segunda capa ya establecido en `esqueleto-monorepo-auth` (aunque aqui no hay RLS de por medio, sino permisos de rol de base de datos, porque quien llama no es un usuario de Supabase Auth).

**El servicio A2A de prueba es desechable: se ejecuta en local para validar el SDK, no se añade a `docker-compose.yml` ni queda como servicio permanente.** Alternativa considerada: dejarlo como cuarto servicio de ejemplo. Se descarta por ruido: añadiria un servicio mas a mantener sin aportar comportamiento que la spec necesite; su unico valor es confirmar pronto, antes de escribir los tres agentes reales, que `a2a-sdk` y el cliente A2A de FastAPI encajan como se espera.

**Limites de tiempo con `asyncio.wait_for` en el orquestador de FastAPI, no en los propios agentes.** Cada llamada A2A sincrona se envuelve en un timeout de 2 minutos; la generacion completa, en uno de 5 minutos medido desde que se crea. Alternativa considerada: que cada agente se autolimite internamente. Se descarta: el orquestador es quien conoce el tiempo ya transcurrido de la generacion completa y es el unico sitio donde aplicar el limite de 5 minutos tiene sentido; duplicar logica de timeout en cuatro sitios (orquestador + 3 agentes) es mas fragil.

**No hay cambios de esquema en `generation`/`exercise`.** Ambas tablas, aplicadas en `esqueleto-monorepo-auth`, ya tienen las columnas que este change necesita (`status`, `error_message`, `kind`, y en `exercise` el candidato con `saved = false` por defecto). Solo hace falta la migracion nueva para el esquema `memory` y los dos roles.

## Risks / Trade-offs

- [Conexion directa a Postgres desde tres agentes mas el backend añade conexiones fuera del pool que gestiona Supabase via PostgREST] → Mantener el pool de conexiones de cada agente pequeño (1-2), y si se vuelve un problema, pasar por el pooler de Supabase (pgbouncer) sin cambiar el contrato de las specs.
- [`a2a-sdk` es una dependencia nueva y poco probada en este proyecto] → El servicio de prueba desechable (primera tarea de este change) valida el cableado antes de construir los tres agentes reales sobre el mismo patron.
- [Si LiteLLM cae, los tres agentes de generacion fallan a la vez porque comparten el mismo proxy] → Ya es una dependencia compartida desde `esqueleto-monorepo-auth` (LiteLLM esta pensado como punto unico de acceso a modelos); no es un riesgo nuevo de este change.
- [Dos roles de Postgres nuevos (`agents_memory`, `agents_exercise_reader`) son credenciales adicionales que gestionar] → Alcance minimo por diseño (un esquema, una tabla de solo lectura); se documentan en `.env.example` igual que las demas.

## Migration Plan

Nueva migracion `infra/supabase/migrations/0003_agents_memory.sql`: crea el esquema `memory`, los roles `agents_memory` (USAGE+CREATE sobre `memory`) y `agents_exercise_reader` (SELECT sobre `public.exercise`), y sus contraseñas via variables de entorno de Supabase al aplicarla (no hardcodeadas en el SQL). Se aplica con `apply_migration` igual que las dos anteriores; no hay datos previos que migrar (greenfield). Las tablas de `langgraph-checkpoint-postgres` dentro de `memory` las crea el propio paquete al arrancar cada agente (`setup()`), no esta migracion.
