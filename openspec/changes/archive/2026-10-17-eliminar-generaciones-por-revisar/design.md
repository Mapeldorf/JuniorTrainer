# Design

## Context

El primer listado de `/ejercicios` (`frontend/src/app/tech-lead/ejercicios/`) muestra las generaciones pendientes que devuelve `GET /generations` (`backend/app/routers/generations.py`): las que estan en `generating` o `ready`. Las `ready` ya tienen candidatos, que son filas de `exercise` con `saved = false` enlazadas por `generation_id`. Guardar un candidato lo vuelve definitivo (`saved = true`) y, en el flujo actual de revision, guardar cierra la generacion (`done`), asi que una generacion `ready` normalmente solo tiene candidatos sin guardar.

Referencias: ver proposal.md - Why para la motivacion y specs/exercise-generation/spec.md para los requisitos.

Esquema relevante (`infra/supabase/migrations/0001_schema.sql`, `0007_repo_access_log.sql`):
- `generation`: `status in ('generating','ready','done','error')`, sin columna de borrado.
- `exercise`: `generation_id uuid not null references generation(id)` (sin cascade), `saved`, `deleted_at`.
- `repo_access_log`: `generation_id uuid not null references generation(id)` (sin cascade).
- `block_exercise` y `assignment_exercise` referencian `exercise(id)` y solo admiten ejercicios `saved = true` (trigger `block_exercise_requires_saved`).

## Goals / Non-Goals

**Goals:**
- Eliminar de forma definitiva una generacion `ready` y todos sus candidatos, de forma atomica.
- Exponer la accion desde el listado de pendientes con el dialogo de confirmacion existente.
- No tocar el catalogo de ejercicios definitivos ni los bloques/asignaciones ya creados.

**Non-Goals:**
- Eliminar generaciones `generating`, `done` ni `error`.
- Cancelar una generacion en curso (seguiria en curso aunque se eliminara su fila).
- Deshacer la eliminacion (no hay papelera).

## Decisions

**D1 - Borrado fisico de la generacion y sus candidatos.**
Se descarta el borrado logico (una columna `deleted_at` en `generation`): el tech lead quiere descartar generaciones que no le interesan y estas no tienen historial que conservar. El borrado fisico mantiene el esquema actual sin columnas nuevas y hace que la generacion desaparezca de cualquier consulta por id.

**D2 - Cascade en las FK para que el borrado sea un unico `DELETE` atomico.**
Migracion nueva que cambia `exercise.generation_id` y `repo_access_log.generation_id` a `on delete cascade`. Asi la eliminacion es una sola sentencia (`DELETE FROM generation WHERE id = ...`): o se borra la generacion con sus candidatos y sus registros de auditoria, o no se borra nada. Alternativa descartada: orquestar varios `DELETE` desde el router (registros de auditoria, luego candidatos, luego generacion) -- no es atomico y un fallo intermedio dejaria una generacion `ready` sin candidatos. Las FK de `block_exercise`/`assignment_exercise` a `exercise` no estorban porque sus filas solo apuntan a ejercicios `saved = true`, que D3 excluye.

**D3 - Se rechaza eliminar una generacion con ejercicios ya guardados.**
Si algun ejercicio de la generacion tiene `saved = true`, la peticion responde 409 y no se borra nada. Protege el catalogo de definitivos: esos ejercicios pueden estar en bloques o en copias de asignacion, que no deben romperse. En el flujo normal esto no ocurre (guardar cierra la generacion a `done`); es una salvaguarda para el caso borde de guardado parcial sin cierre.

**D4 - Solo se puede eliminar una generacion `ready`.**
Mismo criterio que el cierre de revision (`POST /generations/{id}/close`): una generacion `generating` aun no tiene candidatos que descartar y su orquestacion seguiria corriendo en segundo plano, asi que se rechaza con 409; `done`/`error` ya no aparecen en el listado, luego tampoco se pueden eliminar desde el. El boton de la interfaz solo se muestra en `ready` (requisito "Boton de eliminacion en el listado de generaciones por revisar").

**D5 - Endpoint `DELETE /generations/{generation_id}` que responde 204.**
Encaja con la ruta ya existente por id y con el `DELETE` de semanticas REST; 404 si el id no existe, 409 si no esta `ready` o tiene ejercicios guardados, 403 si el rol no es tech lead (`require_tech_lead`). No devuelve cuerpo: la pantalla recarga el listado de pendientes.

**D6 - La interfaz reutiliza `ConfirmDialogService` y el estilo de "Eliminar" ya existente.**
Se anade `deleteGeneration(id)` a `GenerationsApiService`. En `EjerciciosComponent`, un metodo `eliminarGeneracion(generation)` (envuelto con un `confirmarEliminarGeneracion()` sustituible en tests, mismo patron que `eliminar()` de guardados) abre `ConfirmDialogService.confirm({ destructive: true })` con un mensaje que advierte de que se eliminan los ejercicios de esa generacion. El boton se coloca a la derecha de "Revisar", solo bajo `status === 'ready'`, con el mismo tratamiento visual que el "Eliminar" de la tabla de guardados (`text-danger`). Al confirmar y completarse la peticion, se recarga con `loadPending()`; si falla, se muestra el error de la pantalla.

## Risks / Trade-offs

- [Se eliminan los registros de auditoria de GitHub de la generacion borrada] -> Aceptado: la auditoria registra accesos durante una generacion que deja de existir; conservarla exigiria mantener filas huerfanas o una generacion tombstone, fuera del alcance elegido por el usuario.
- [El cascade en `exercise.generation_id` permite borrar ejercicios guardados si alguna otra ruta borrara la generacion] -> Solo este endpoint borra generaciones, y D3 rechaza antes el caso con `saved = true`; el riesgo de una carrera (guardar justo entre la comprobacion y el borrado) es despreciable en esta app de un solo tech lead.
- [Guardado parcial sin cierre deja una generacion `ready` con ejercicios guardados que ya no se puede eliminar] -> Es el comportamiento buscado: primero se debe cerrar la revision; la interfaz muestra el 409 como error.
- [El boton se ofrece solo en `ready`: no se puede descartar una generacion que se quedo en `generating`] -> Fuera de alcance; una generacion atascada en curso se resuelve por los limites de tiempo existentes, que la llevan a `error`.

## Migration Plan

- Una migracion nueva (`0008_*`) que recrea las FK de `exercise.generation_id` y `repo_access_log.generation_id` con `on delete cascade`. No hay backfill ni datos que transformar.
- Despliegue: backend (endpoint nuevo) y migracion deben ir juntos; el frontend solo depende del endpoint nuevo, asi que puede desplegarse con el mismo release.
- Rollback: revertir la migracion (recrear las FK sin cascade) y el endpoint; no hay estado que migrar de vuelta.

## Open Questions

- Ninguna que cambie el alcance, los specs o el desglose de tareas.