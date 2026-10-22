# Proposal

## Why

El agente de ejercicios evita repetir temas con dos mecanismos solapados: una memoria propia sin TTL en Postgres (`app/memory.py`, hasta 20 enunciados recientes por tipo) y una consulta de solo lectura a `public.exercise` (solo `saved = true`). La memoria propia acumula **todos** los candidatos generados, aceptados o no, lo que hace crecer el prompt del LLM (y su coste/latencia) mas rapido que el ritmo real de aceptacion, y cada escritura reescribe el blob completo del historial. Sin conceder al agente ningun permiso de escritura nuevo, se puede cubrir el mismo requisito consultando unicamente la base de datos, ampliando esa consulta para que tambien incluya los ejercicios eliminados (no solo los guardados), que hoy quedan fuera y podrian repetirse.

## What Changes

- **BREAKING**: se elimina `app/memory.py` (store `exercise_history` sin TTL) y su uso en `generate_exercises` (`get_recent_statements`/`save_statements`). El agente de ejercicios deja de tener memoria propia.
- `search_saved_exercises` pasa a devolver tambien los ejercicios con `deleted_at` no nulo, ademas de los `saved = true`, para que la lista de "enunciados a evitar" cubra ambos casos sin necesitar una segunda fuente.
- El `limit` de esa consulta sube de 10 a 200: se evita repetir el tema de los 200 ejercicios (guardados o eliminados) mas recientes de ese tipo, en vez de los 20 que cubria la memoria propia eliminada.
- El campo `memory_hit` de `ExerciseGenerationResult` pasa a reflejar si la consulta a `public.exercise` devolvio algun resultado (guardado o eliminado), en vez de depender de la memoria propia.
- No se concede ningun permiso de escritura nuevo al agente: sigue usando exclusivamente el rol de solo lectura `agents_exercise_reader`. El rol `agents_memory` deja de ser necesario para este agente (sigue en uso por los agentes web y de codigo).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `agent-memory`: el requisito "El agente de ejercicios no repite temas ya propuestos" deja de basarse en un historial propio del agente; pasa a basarse unicamente en una consulta a los ejercicios guardados y eliminados en base de datos.

## Impact

- `agents/exercises/app/memory.py`: se elimina el fichero completo.
- `agents/exercises/app/service.py`: se elimina el uso de `get_recent_statements`/`save_statements`; `avoid_statements` pasa a construirse solo con el resultado de `search_saved_exercises`.
- `agents/exercises/app/tools/saved_exercises.py`: la consulta SQL deja de filtrar por `saved = true` en exclusiva; incluye tambien las filas con `deleted_at is not null`.
- `agents/exercises/app/db.py`: se elimina `conn_string()` (rol `agents_memory`), que queda sin ningun llamador en este agente. `exercise_reader_conn_string()` no cambia.
- `agents/exercises/app/config.py`: se elimina el campo `agents_memory_password`, que deja de leerse. `agents_exercise_reader_password` y el resto de `agents_pg_*` no cambian. El rol `agents_memory` y su migracion (`infra/supabase/migrations/0003_agents_memory.sql`) no se tocan: siguen en uso por los agentes web y de codigo.
- Pruebas/scripts de verificacion que dependan de la memoria propia del agente de ejercicios (`scripts/verify_no_repeated_themes.py`, `scripts/verify_trace_id.py`, `scripts/verify_saved_exercises.py`) se revisan para no depender de `app/memory.py` ni del contrato antiguo "solo guardados".
- `agents/exercises/requirements.txt`: se eliminan `langgraph` y `langgraph-checkpoint-postgres`, que solo los usaba `app/memory.py` (verificado: ninguna otra parte del agente los importa).
