# Proposal

## Why

El agente web envuelve `research()` en un grafo de LangGraph de un solo nodo solo para poder usar un checkpoint `AsyncPostgresSaver` (`agents/web/app/checkpoint.py`) que se crea y se borra dentro de la misma llamada a `research_with_checkpoint`, dentro de la misma tarea A2A. Nada en el flujo (`executor.py`) vuelve a leer ese checkpoint ni reanuda ningun paso: la busqueda en Tavily se hace una vez y su resultado se pasa directo al agente de ejercicios. Esta memoria de corto plazo no aporta ningun comportamiento observable hoy, añade dos round-trips a Postgres por tarea (setup + borrado) y una dependencia mas (`langgraph-checkpoint-postgres` para este uso concreto), y fue la causa directa de un bug ya corregido en Windows (`psycopg.InterfaceError` con `ProactorEventLoop`) documentado en el `design.md` de la spec archivada `2026-10-12-generacion-ejercicios-agentes`.

## What Changes

- Eliminar el checkpoint de LangGraph/`AsyncPostgresSaver` del agente web: `research_with_checkpoint` deja de compilar y ejecutar un grafo de un solo nodo, y llama directamente a `research()`.
- Eliminar el modulo `agents/web/app/checkpoint.py` (incluida `count_checkpoints`, usada solo para verificacion manual de esta memoria) y su script de verificacion `agents/web/scripts/verify_short_term_memory.py`.
- Actualizar `executor.py` para llamar a `research()` (o a la funcion que la sustituya) sin pasar por `research_with_checkpoint`.
- Quitar la dependencia `langgraph-checkpoint-postgres` de `agents/web/requirements.txt` si ningun otro modulo del agente web la usa.
- **BREAKING** (solo interno): cualquier script o test que importe `app.checkpoint` deja de funcionar; no afecta a la API A2A ni al contrato con el orquestador.

Fuera de alcance: la memoria de largo plazo del agente web (`PostgresStore`, cache de busquedas por tecnologia) y el mismo patron en los agentes de codigo/ejercicios, que no se tocan en este cambio.

## Capabilities

Este cambio no modifica ningun requisito observable de `agent-memory` ni de ninguna otra spec: la memoria de corto plazo eliminada no implementaba ningun requisito descrito en specs (la reutilizacion de busquedas, la marca de `memory_hit` en la traza y el resto de comportamiento de memoria siguen intactos via la memoria larga, sin cambios). Es una simplificacion de implementacion pura.

### New Capabilities

(ninguna)

### Modified Capabilities

(ninguna — ver justificacion arriba; `skip_specs: true` en `.openspec.yaml`)

## Impact

- `agents/web/app/checkpoint.py`: eliminado.
- `agents/web/app/executor.py`: deja de importar `research_with_checkpoint`; llama a `research()` directamente.
- `agents/web/app/service.py`: sin cambios de contrato (sigue exponiendo `research()` y `WebResearchResult`).
- `agents/web/scripts/verify_short_term_memory.py`: eliminado (verificaba el checkpoint que desaparece).
- `agents/web/requirements.txt`: se retira `langgraph-checkpoint-postgres` si queda sin uso.
- Esquema `memory` de Postgres: deja de recibir escrituras/borrados de checkpoints de LangGraph para el agente web (la tabla de checkpoints de LangGraph puede quedar vacia o sin uso para este agente; no se elimina la migracion del esquema porque la memoria larga sigue usandolo).
- Sin impacto en la API A2A del agente web ni en el orquestador: la skill `investigar_tecnologias` devuelve el mismo `WebResearchResult`.
