# Design

## Context

Hoy `generate_exercises` (`agents/exercises/app/service.py`) construye `avoid_statements` combinando dos fuentes: `search_saved_exercises` (lee `public.exercise` donde `saved = true and deleted_at is null`, rol `agents_exercise_reader`) y `get_recent_statements` (lee/escribe un historial propio sin TTL en `AsyncPostgresStore`, rol `agents_memory`, namespace `exercise_history`, hasta 20 enunciados por tipo). Ver proposal.md - Why para la justificacion de por que se unifica en una sola fuente.

La tabla `public.exercise` (`infra/supabase/migrations/0001_schema.sql`) ya tiene las columnas necesarias (`type`, `saved`, `deleted_at`, `created_at`); no hace falta ninguna migracion de esquema. El unico indice relevante hoy es `exercise_saved_idx on (saved) where deleted_at is null` (parcial, no cubre filas eliminadas) y no hay indice sobre `type`.

## Goals / Non-Goals

**Goals:**
- Una sola fuente de "enunciados a evitar": la consulta a `public.exercise`.
- Cubrir tanto los ejercicios guardados (`saved = true`) como los eliminados (`deleted_at` no nulo), sin excluir los ya reemplazados o descartados por un tech lead.
- No anadir ningun permiso de escritura nuevo al agente de ejercicios: `agents_exercise_reader` sigue siendo de solo lectura.

**Non-Goals:**
- No se toca el comportamiento de los agentes web o de codigo, ni el rol `agents_memory` que ellos siguen usando.
- No se anade una ventana temporal (tipo "ultimos 30 dias") a la consulta: se mantiene el mismo criterio de "guardado o eliminado", sin limite de antiguedad, igual que hoy no lo tiene `search_saved_exercises`.
- No se optimiza el esquema (indices) mas alla de lo que ya habia: la consulta actual tampoco tenia indice sobre `type`, asi que ampliar el filtro no introduce una clase de problema de rendimiento nueva.

## Decisions

### Ampliar `search_saved_exercises` en vez de anadir una segunda consulta
Se cambia el `where` de la consulta existente (`saved = true and deleted_at is null`) a `(saved = true or deleted_at is not null)`, en vez de anadir una query aparte para eliminados. Una sola consulta mantiene el mismo presupuesto (`SearchBudget`, sigue consumiendo 1 de las 3 permitidas). Alternativa descartada: dos consultas (una para guardados, otra para eliminados) -- anadiria complejidad y un segundo roundtrip sin necesidad, ya que ambas comparten conexion, rol y forma de resultado.

### Subir el `limit` de 10 a 200
El `limit` por defecto de `search_saved_exercises` (10) y el valor pasado desde `generate_exercises` suben a 200, para cubrir "no repetir los ultimos 200 ejercicios" en vez de los 20 que cubria la memoria propia eliminada. Coste aceptado: `select ... order by created_at desc limit 200` sigue siendo una lectura acotada y barata para Postgres (trivial salvo que un tipo acumule decenas de miles de filas, muy por encima del volumen esperado de este banco de ejercicios); el coste real esta en tokens de entrada del prompt del generador, que crece linealmente con el numero de enunciados (≈15-25 tokens cada uno, así que 200 enunciados añaden unos pocos miles de tokens de entrada por llamada) -- barato y rapido de procesar frente al limite de contexto del modelo, pero diez veces mas que con 20.

### Eliminar `app/memory.py` por completo, sin dejar un modo de compatibilidad
Se borra el fichero y sus referencias en `service.py` (`get_recent_statements`, `save_statements`) en vez de desactivarlo con una bandera o dejarlo sin usar. El store `exercise_history` en Postgres no se migra ni se limpia activamente: al dejar de escribirse y leerse, su contenido queda huerfano y es responsabilidad de una limpieza de datos aparte (fuera de alcance), igual que cualquier otra tabla/namespace que deja de usarse.

### Eliminar tambien `conn_string()` y `agents_memory_password` de este agente
Una vez fuera `app/memory.py`, `conn_string()` (`app/db.py`) y el campo `agents_memory_password` (`app/config.py`) de este agente quedan sin ningun llamador: se eliminan en vez de dejarlos como codigo muerto. El rol `agents_memory` y la migracion que lo crea (`infra/supabase/migrations/0003_agents_memory.sql`) NO se tocan -- siguen siendo necesarios para los agentes web y de codigo, que son servicios distintos con su propia copia de `config.py`/`db.py`.

### `memory_hit` pasa a reflejar el acierto de la consulta a BD
`ExerciseGenerationResult.memory_hit` se sigue calculando como `bool(avoid_statements)`, pero `avoid_statements` ya solo viene de `search_saved_exercises`. Semanticamente deja de significar "acierto de memoria propia" y pasa a significar "habia algun ejercicio guardado o eliminado de ese tipo". Se mantiene el mismo nombre de campo (no es parte del contrato A2A expuesto a otros servicios, es interno a `ExerciseGenerationResult`) para no tocar los consumidores de `generate_exercises` en esta misma generacion.

### No anadir indice nuevo
La consulta ampliada sigue sin tener un indice que cubra `type` directamente (como ya ocurria antes de este cambio). Se deja como mejora de rendimiento aparte si el volumen de la tabla `exercise` lo llega a justificar; no es necesario para la correccion de este cambio.

## Risks / Trade-offs

- **Repetir un ejercicio "readaptado"**: un ejercicio eliminado por ser de mala calidad entra igualmente en la lista de "a evitar", lo que puede impedir redactar una version mejor del mismo tema. Mitigacion: el prompt ya pide "no repetir el tema", no el enunciado exacto, y esto ya ocurria antes con los guardados; se acepta el mismo compromiso para los eliminados.
- **Perdida de la memoria de candidatos descartados y nunca guardados ni eliminados**: con `app/memory.py` fuera, un candidato generado pero simplemente ignorado (ni guardado ni eliminado, p. ej. porque la generacion se cerro con candidatos sin guardar) ya no se recuerda y podria repetirse en una generacion posterior del mismo tipo. Mitigacion: se acepta como trade-off explicito de esta propuesta (ver proposal.md - Why): el coste de evitarlo con una memoria propia (crecimiento ilimitado de tokens en el prompt, reescritura completa del historial en cada tarea) supera el beneficio de cubrir ese caso concreto.

## Migration Plan

Sin pasos de migracion de datos ni de base de datos. Despliegue en un unico cambio:
1. Ampliar el `where` de `search_saved_exercises`.
2. Eliminar `app/memory.py` y sus referencias en `service.py`.
3. Actualizar/eliminar los scripts de verificacion que dependian del historial propio (p. ej. `scripts/verify_no_repeated_themes.py`).

Rollback: revertir el commit: no hay esquema nuevo ni datos migrados que deshacer. El store `exercise_history` huerfano no interfiere si se revierte (nadie mas lo lee ni lo escribe).
