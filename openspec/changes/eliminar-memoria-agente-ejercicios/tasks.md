# Tasks

## 1. Ampliar la consulta a base de datos

- [x] 1.1 Cambiar el `where` de `search_saved_exercises` (`agents/exercises/app/tools/saved_exercises.py`) de `saved = true and deleted_at is null` a `(saved = true or deleted_at is not null)`, y verificar con una consulta manual (o test) que devuelve tanto ejercicios guardados como eliminados del tipo pedido, y ninguno que no sea ni lo uno ni lo otro -- verificado en vivo contra Supabase real (solo lectura): la consulta ampliada corre sin error y devuelve los 15 `knowledge` guardados existentes; no hay ningun eliminado todavia en esa base para comprobar esa rama en vivo, pero el SQL (`saved = true or deleted_at is not null`) es directo
- [x] 1.2 Subir el `limit` por defecto de `search_saved_exercises` de 10 a 200, y el valor pasado desde `generate_exercises` (`agents/exercises/app/service.py`) de `limit=10` a `limit=200`; verificar que una consulta con mas de 10 filas del tipo pedido devuelve hasta 200
- [x] 1.3 Actualizar el docstring del modulo y de `_QUERY` para reflejar que ya no se limita a `saved = true` y que el limite es 200

## 2. Eliminar la memoria propia del agente

- [x] 2.1 Eliminar el fichero `agents/exercises/app/memory.py`
- [x] 2.2 En `agents/exercises/app/service.py`, quitar el import y el uso de `get_recent_statements`/`save_statements`; `avoid_statements` pasa a ser directamente `saved_statements` (el resultado de `search_saved_exercises`). Verificar que `generate_exercises` sigue compilando y que `avoid_statements`/`memory_hit` se derivan solo de esa lista -- verificado con `py_compile` e import real del modulo
- [x] 2.3 Eliminar `conn_string()` de `agents/exercises/app/db.py` y el campo `agents_memory_password` de `agents/exercises/app/config.py`; verificar que no queda ninguna referencia (`grep -r agents_memory agents/exercises/app`) -- grep limpio salvo comentarios explicativos del cambio; `Settings()` carga en real sin ese campo

## 3. Actualizar scripts de verificacion

- [ ] 3.1 Reescribir `agents/exercises/scripts/verify_no_repeated_themes.py` para sembrar el "ya propuesto" insertando directamente en `public.exercise` (una fila guardada y otra eliminada, via la API REST de Supabase con la service_role key) en vez de depender de dos llamadas seguidas a `generate_exercises`; verificar ejecutandolo contra una base de datos real y comprobando que `memory_hit` es `true` y que los enunciados generados no repiten el tema sembrado -- reescrito y verificado por `py_compile`/import; **no ejecutado end-to-end** (necesita LiteLLM levantado para la llamada real al modelo, y la llamada REST de siembra fallo por un problema de verificacion TLS del entorno de este agente de IA, no del codigo -- pendiente de ejecutar por el equipo con LiteLLM arriba)
- [x] 3.2 Revisar `verify_exercise_generation.py`, `verify_statement_limit.py`, `verify_trace_id.py` y `verify_saved_exercises.py` por si referencian `app/memory.py`, `get_recent_statements`, `save_statements` o el contrato antiguo "solo guardados"; actualizarlos si lo hacen -- `verify_exercise_generation.py`/`verify_statement_limit.py` no referenciaban nada de eso (sin cambios); `verify_trace_id.py` reescrito (ya no asume memory_hit=false en la 1a llamada, siembra un ejercicio para el caso determinista); `verify_saved_exercises.py` actualizado (su contrato ahora es "guardado o eliminado", no solo "guardado") y ejecutado en vivo con exito contra Supabase real

## 4. Verificacion final

- [ ] 4.1 Ejecutar `python -m scripts.verify_no_repeated_themes` desde `agents/exercises/` contra Postgres real y confirmar que una generacion respeta la exclusion de temas guardados y eliminados, sin ningun fallo de import de `app/memory.py` -- pendiente (ver nota de 3.1): requiere LiteLLM levantado, no ejecutado en este entorno
- [x] 4.2 Confirmar en el arranque del servicio (`run.py`) que no hace falta `AGENTS_MEMORY_PASSWORD` para que el agente de ejercicios levante correctamente -- confirmado instanciando `Settings()` en real: carga sin ese campo
