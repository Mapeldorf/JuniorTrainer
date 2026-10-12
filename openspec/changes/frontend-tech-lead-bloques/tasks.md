# Tasks

## 1. Backend: listado y detalle de bloques (exercise-blocks)

- [x] 1.1 `backend/app/schemas/block.py`: anadir `resolved: bool` a `BlockSummary` y a `BlockDetail`, y `exercise_deleted: bool` a `BlockExerciseItem`; anadir `assigned_students: list[{id: str, name: str}]` a `BlockSummary`
- [x] 1.2 `backend/app/routers/blocks.py`: en `list_blocks`, calcular `resolved` (reusando `_block_has_answers`, adaptada para resolver todos los bloques de la pagina en una sola consulta en vez de bloque a bloque) y `assigned_students` con una consulta de `assignment.select("block_id, student_id, profile:student_id(name)")` filtrada por los ids de bloques devueltos (design.md - decision D1/D2); verificar con un test o script que un bloque sin asignaciones devuelve `assigned_students: []` y `resolved: false`, y uno con una respuesta registrada en cualquiera de sus asignaciones devuelve `resolved: true`
- [x] 1.3 `backend/app/routers/blocks.py`: en `get_block`/`_get_block_detail`, anadir `deleted_at` a la proyeccion del join `block_exercise.select("position, exercise:exercise_id(...)")` y derivar `exercise_deleted` por fila sin incluir `deleted_at` en `SavedExercise` (design.md - decision D3); anadir `resolved` al detalle con la misma funcion de la tarea 1.2; verificar con un test o script que un bloque con un ejercicio eliminado de la app marca solo esa fila como `exercise_deleted: true`, sin afectar al resto de la composicion

## 2. Backend: conteo de uso en el catalogo (exercise-catalog)

- [x] 2.1 `backend/app/schemas/exercise.py`: anadir `block_usage_count: int` a `SavedExerciseListItem` (nunca a `SavedExercise`, design.md - decision D4)
- [x] 2.2 `backend/app/routers/exercises.py`: en `list_exercises` (o el handler de `GET /exercises`), calcular `block_usage_count` agrupando `block_exercise` por `exercise_id` sobre los ids de la pagina devuelta; verificar con un test o script que un ejercicio sin usar devuelve `0` y uno usado en varios bloques devuelve el conteo correcto

## 3. Backend: progreso detallado por alumno (block-assignment)

- [x] 3.1 `backend/app/schemas/block.py`: anadir `type` y `statement` a `ExerciseProgress`, y `answer_text`/`justification` (nullable, solo si `answered`) junto al `verdict` ya existente
- [x] 3.2 `backend/app/routers/blocks.py`: en `get_block_progress`, ampliar la consulta de `assignment_exercise` para unir `exercise.type`/`exercise.statement` y la de `answer` para incluir `answer_text`/`justification`, leyendo siempre desde la copia de cada asignacion (`assignment_exercise`/`answer`), nunca desde la composicion actual del bloque (design.md - decision D5); verificar con un test o script que, tras editar un bloque entre dos asignaciones distintas (sin respuestas aun), el progreso de cada alumno sigue mostrando el enunciado de su propia copia

## 4. Verificacion de backend contra la base real

- [x] 4.1 Ejecutar (o extender) un script de verificacion end-to-end contra el backend real: crear un bloque, asignarlo a un alumno, responder un ejercicio, confirmar que `GET /blocks` marca `resolved: true` y muestra al alumno en `assigned_students`, que `GET /blocks/{id}` marca `resolved: true` y, si se elimina uno de sus ejercicios del catalogo, lo marca `exercise_deleted: true`, que `GET /exercises` refleja el conteo de bloques correcto, y que `GET /blocks/{id}/assignments` devuelve tipo/enunciado/respuesta/justificacion por ejercicio; limpiar los datos de prueba al terminar

## 5. Cliente HTTP de bloques

- [x] 5.1 `frontend/src/app/core/blocks-api.model.ts`: DTOs de `GET /blocks`, `POST /blocks`, `GET /blocks/{id}`, `PATCH /blocks/{id}`, `DELETE /blocks/{id}`, `POST /blocks/{id}/assignments` y `GET /blocks/{id}/assignments`, con los campos nuevos de los grupos 1-3; verificar que `npx tsc --noEmit` compila sin errores
- [x] 5.2 `frontend/src/app/core/blocks-api.service.ts`: `BlocksApiService` nuevo (design.md - decision D6, mismo patron que `AssignmentsApiService`/`GenerationsApiService`) con `list(deleted?)`, `create(...)`, `getDetail(id)`, `update(id, ...)`, `delete(id)`, `assign(id, studentIds)`, `getProgress(id)`; verificar con `provideHttpClientTesting` que cada metodo llama al endpoint, metodo HTTP y URL correctos
- [x] 5.3 `frontend/src/app/core/generations-api.model.ts` y `.service.ts`: anadir `block_usage_count` a `SavedExerciseListItem` y confirmar que `listSaved` ya lo propaga sin cambios adicionales; verificar que el test existente de `listSaved` sigue pasando con el campo nuevo en los datos de prueba

## 6. Activar pestaña y pantalla "Bloques de ejercicios" (5)

- [x] 6.1 `frontend/src/app/tech-lead/tech-lead-nav/tech-lead-nav.ts`/`.html`: activar la pestaña "Bloques de ejercicios" (enlazada a `/bloques`, deja de estar deshabilitada; "Alumnos" sigue "Proximamente"); verificar con un test que esa pestaña ya es clicable (tiene `routerLink`) y la de "Alumnos" sigue sin serlo
- [x] 6.2 Componente standalone `frontend/src/app/tech-lead/bloques/bloques.ts` + `.html`: incluye `TechLeadNavComponent`; carga `BlocksApiService.list()` para la tabla de bloques activos (nombre, numero de ejercicios, alumnos asignados, badge "Resuelto - no editable" cuando `resolved`, acceso al detalle) y `BlocksApiService.list(true)` para la seccion colapsable "Bloques de ejercicios eliminados (N)" (fecha de eliminacion y enlace "Ver resultados"); boton "Nuevo bloque de ejercicios" (navega a `/bloques/nuevo`); estado vacio con mensaje invitando a crear el primero
- [x] 6.3 Registrar la ruta `bloques` (guardada por `authGuard` + `techLeadGuard`) en `app.routes.ts`; verificar con `npx vitest run` que el componente renderiza bloques activos y eliminados a partir de datos de prueba, y que el estado vacio aparece sin bloques

## 7. Pantalla "Nuevo/editar bloque de ejercicios" (6)

- [x] 7.1 Componente standalone `frontend/src/app/tech-lead/bloque-editar/bloque-editar.ts` + `.html` (design.md - decision D7): lee un `blockId` opcional de la ruta; sin id, formulario vacio con boton "Crear bloque"; con id, precarga `BlocksApiService.getDetail(blockId)` (nombre + ejercicios marcados) con boton "Guardar cambios"
- [x] 7.2 Selector de ejercicios guardados: checklist filtrable por tipo y buscable por texto (reusa `GenerationsApiService.listSaved` con sus filtros ya existentes), cada fila muestra enunciado, procedencia y `block_usage_count` ("Sin usar"/"En N bloque(s)"); al editar, una fila cuyo ejercicio tiene `exercise_deleted: true` se marca "Eliminado" y deshabilita el boton de guardar hasta que se desmarque
- [x] 7.3 Panel lateral: conteo de ejercicios por tipo y total, recordatorio del rango permitido (1-100), boton crear/guardar (deshabilitado con 0 marcados o con algun eliminado sin desmarcar, segun `BlockCreateRequest`/`BlockUpdateRequest`) y boton cancelar (vuelve a `/bloques` o al detalle si viene de editar); verificar con un test que el boton esta deshabilitado en ambos casos y habilitado cuando hay al menos un ejercicio marcado y ninguno eliminado
- [x] 7.4 Registrar las rutas `bloques/nuevo` y `bloques/:blockId/editar` (guardadas por `authGuard` + `techLeadGuard`) en `app.routes.ts`; verificar con `npx vitest run` el componente en modo creacion y en modo edicion (precargado, incluyendo el caso con un ejercicio eliminado)

## 8. Pantalla "Detalle del bloque y asignacion" (7, 7b)

- [x] 8.1 Componente standalone `frontend/src/app/tech-lead/bloque-detalle/bloque-detalle.ts` + `.html`: carga `BlocksApiService.getDetail(blockId)`; cabecera con nombre, fecha de creacion, numero de ejercicios; botones "Editar bloque" (navega a `/bloques/:id/editar`, deshabilitado si `resolved`) y "Eliminar bloque" (`BlocksApiService.delete`, con confirmacion); aviso fijo explicando que editar/eliminar solo afecta a asignaciones futuras y que un bloque se vuelve "resuelto" cuando algun alumno ha respondido todos sus ejercicios
- [x] 8.2 Seccion "Alumnos asignados (N)": carga `BlocksApiService.getProgress(blockId)`; buscable por nombre; cada alumno es un desplegable con su resumen (estado, "X de Y respondidas", contadores de correctas/incompletas/incorrectas) y, al abrir, el detalle de cada ejercicio (tipo, enunciado, respuesta, veredicto, justificacion, o "Sin responder"); verificar con un test que el resumen y el detalle expandido muestran los datos nuevos de la tarea 3.1
- [x] 8.3 Seccion "Asignar a mas alumnos": checklist de alumnos sin este bloque todavia (derivado de la lista de alumnos del backend menos los ya presentes en `assigned_students`/progreso) y boton "Asignar" (`BlocksApiService.assign`); seccion de solo lectura "Ejercicios del bloque" con la composicion ordenada (tipo + enunciado); ambas secciones, junto con "Editar"/"Eliminar", se ocultan cuando el bloque esta eliminado (`deleted_at` no nulo), dejando la vista en modo solo lectura para la pantalla 7b (design.md - decision D8); verificar con un test que un bloque eliminado no muestra "Editar"/"Eliminar"/"Asignar a mas alumnos". La lista de alumnos se sirve de `GET /users` (capacidad `user-auth`, ya implementada, sin cambios de backend); no habia cliente frontend para ese endpoint, asi que esta tarea crea `frontend/src/app/core/users-api.model.ts`/`.service.ts` (mismo patron de servicio-por-capacidad), con su `provideHttpClientTesting`
- [x] 8.4 Registrar la ruta `bloques/:blockId` (guardada por `authGuard` + `techLeadGuard`) en `app.routes.ts`, y enlazar "Ver detalle" (pantalla 5, bloques activos) y "Ver resultados" (pantalla 5, bloques eliminados) a la misma ruta; verificar con `npx vitest run` el componente en los tres estados (normal, resuelto, eliminado)

## 9. Verificacion de extremo a extremo

- [x] 9.1 Pedir al usuario que ejecute `ng serve` (frontend) junto al backend real y haga, como tech lead, el flujo completo: crear un bloque, verlo en el listado, asignarlo a un alumno, editarlo (anadiendo/quitando ejercicios) antes de que tenga respuestas, confirmar que tras responder un ejercicio como alumno el bloque aparece "Resuelto - no editable" y el boton "Editar bloque" se deshabilita, eliminar el bloque y confirmar que pasa a la seccion de eliminados en solo lectura
- [x] 9.2 Pedir al usuario que confirme que un ejercicio eliminado del catalogo (pantalla 2) aparece marcado "Eliminado" si se intenta editar un bloque que lo contiene, y que el conteo "En N bloque(s)" del selector de la pantalla 6 es correcto
- [x] 9.3 Ejecutar `npx vitest run` (frontend) y confirmar que toda la suite pasa, y ejecutar la suite de tests de backend existente para confirmar que los ajustes de los grupos 1-3 no rompen nada ya cubierto

## Workflow follow-up

- Abrir una rama `change/frontend-tech-lead-bloques` y un PR hacia `develop` cuando los grupos 1-9 esten completos y verificados.
- Archivar el change (sincronizando los deltas de `exercise-blocks`, `block-assignment` y `exercise-catalog` en sus specs existentes) una vez el PR este aprobado.
