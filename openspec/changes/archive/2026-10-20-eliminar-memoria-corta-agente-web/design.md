# Design

## Context

`agents/web/app/checkpoint.py` envuelve `research()` (`app/service.py`) en un `StateGraph` de LangGraph de un solo nodo (`research` → `END`), compilado con un `AsyncPostgresSaver` cuyo `thread_id` es `f"{task_id}:web"`. `research_with_checkpoint()` invoca ese grafo y, en un `finally`, borra el thread completo (`adelete_thread`) tanto si la tarea termina bien como si lanza una excepcion. `WebAgentExecutor.execute()` (`app/executor.py`) es el unico punto de entrada real y llama siempre a `research_with_checkpoint`, nunca a `research()` directamente; el grafo nunca se reanuda entre llamadas ni se inspecciona a mitad de tarea. Ver `proposal.md` para la motivacion (overhead sin beneficio observable + bug de Windows ya corregido).

Este checkpoint comparte la cadena de conexion (`app/db.py: conn_string()`) y el fix de event loop de Windows (`app/__init__.py`) con la memoria larga (`app/memory.py`, `AsyncPostgresStore`), que SI se mantiene: ambos modulos usan el mismo rol `agents_memory` sobre el esquema `memory` de Postgres via `psycopg` en modo async.

## Goals / Non-Goals

**Goals:**
- Quitar el grafo de LangGraph, el `AsyncPostgresSaver` y el ciclo escribir/borrar por tarea del agente web, sin cambiar el resultado que `WebAgentExecutor` devuelve al orquestador.
- Dejar `agents/web/app/db.py` y `agents/web/app/__init__.py` correctos tras la eliminacion: siguen siendo necesarios para la memoria larga, pero sus comentarios ya no deben atribuir su razon de ser al checkpoint que desaparece.
- Actualizar los scripts de verificacion manual que dependen de `app.checkpoint` para que sigan siendo utiles sin ese modulo.

**Non-Goals:**
- No se toca la memoria larga (`app/memory.py`, cache de busquedas por tecnologia) ni el requisito de `memory_hit`.
- No se replica ni se discute aqui el mismo patron en los agentes de codigo/ejercicios (fuera de alcance, ver proposal.md).
- No se cambia el contrato A2A del agente web (`WebResearchResult`, skill `investigar_tecnologias`).
- No se añade ningun mecanismo de reintento o resumption a cambio del que se quita: hoy no existe tal comportamiento y no se esta pidiendo.

## Decisions

### Eliminar `checkpoint.py` en vez de simplificarlo
Se considero dejar `research_with_checkpoint` como alias fino de `research()` (por si algo externo lo importa) en vez de borrar el modulo. Se descarta: solo lo importan `executor.py` y los dos scripts de verificacion de este mismo agente, todos en este repo y todos se actualizan en este cambio. Mantener un modulo que ya no envuelve nada seria la abstraccion innecesaria que se esta quitando.

### `executor.py` llama a `research()` directamente
`WebAgentExecutor.execute()` pasa a importar `research` de `app.service` y a llamarla con `(technologies, trace_id)`, sin `task_id` (que solo servia para construir el `thread_id` del checkpoint). `context.task_id` sigue usandose en el mensaje de respuesta A2A (`new_data_message(..., task_id=context.task_id)`), eso no cambia.

### Los scripts de verificacion pierden su aserto sobre checkpoints, no se eliminan todos
- `verify_short_term_memory.py` verificaba exclusivamente el borrado del checkpoint: se elimina, no hay nada que reemplazar (no queda comportamiento de corto plazo que verificar).
- `verify_trace_id.py` verifica trazas de Langfuse, un comportamiento que sigue existiendo: se actualiza para llamar a `research(technologies, trace_id)` en vez de `research_with_checkpoint(task_id, technologies, trace_id)`, quitando el `task_id` sintetico que generaba solo para este fin.

### `conn_string()` y el fix de Windows se quedan, con su comentario corregido
Ambos siguen siendo necesarios para `AsyncPostgresStore` (memoria larga). Se actualiza el docstring de `app/db.py` (ya no comparte uso con `app/checkpoint.py`, que desaparece) y la referencia a `langgraph-checkpoint-postgres` en `app/__init__.py` para que apunte a la razon real que queda: el modo async de `psycopg` que usa `AsyncPostgresStore` en `app/memory.py`. No se toca la logica de ninguno de los dos modulos.

### `langgraph-checkpoint-postgres` se queda en `requirements.txt`
Se planteo retirarla si quedaba sin uso tras los cambios anteriores. Al implementar se confirmo que **no** puede retirarse: el paquete pip `langgraph-checkpoint-postgres` es el mismo distributable que provee tanto `langgraph.checkpoint.postgres` (lo que se elimina) como `langgraph.store.postgres` (`AsyncPostgresStore`, que `app/memory.py` sigue usando para la memoria larga) -- no son dos paquetes independientes. Se verifico leyendo el `RECORD` del paquete instalado en `.venv`. La linea se mantiene sin cambios en `requirements.txt`.

## Risks / Trade-offs

- [Algun otro agente o script fuera de `agents/web/` importa `app.checkpoint` de este agente] → Improbable (cada agente de generacion es un proceso/paquete Python independiente, sin imports cruzados); se confirma con un `grep` del repo completo antes de borrar el fichero, no solo dentro de `agents/web/`.
- [Si en el futuro el grafo del agente web se vuelve multi-nodo (ej. busqueda + verificacion + resumen como pasos separados), reanudar tras un fallo parcial requeriria volver a introducir un checkpoint] → Aceptado: no hay ningun plan concreto de ese cambio hoy; si llega, se re-evalua como una nueva propuesta con esa necesidad real documentada, en vez de mantener la infraestructura de antemano.
- [Retirar `langgraph-checkpoint-postgres` de `requirements.txt` rompe el build si algo la necesitaba indirectamente] → Mitigado verificando con `pip check`/`grep` tras el cambio, antes de darlo por cerrado (ver tasks.md).

## Migration Plan

No hay migracion de datos: los checkpoints eran efimeros (se borraban siempre al terminar cada tarea), asi que no hay fila huerfana que limpiar en `memory.checkpoints`/`memory.checkpoint_blobs`/`memory.checkpoint_writes` al desplegar este cambio. El despliegue es el habitual del agente web (build + redeploy del servicio); no requiere pasos de rollback especiales mas alla de revertir el commit si algo falla, ya que no se modifica el esquema de Postgres ni el contrato A2A.
