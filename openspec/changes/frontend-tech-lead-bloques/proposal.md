# Proposal

## Why

El tech lead ya puede generar y guardar ejercicios (pantalla 2, change archivado "frontend-tech-lead-ejercicios") y el backend ya soporta crear, editar, eliminar y asignar bloques de ejercicios con copia inmutable por alumno (paso 3, change archivado "bloques-asignaciones"), pero no existe ninguna pantalla para ello: hoy un bloque solo se puede componer, asignar o revisar tocando la base de datos a mano. Sin esto, un ejercicio guardado nunca llega a un alumno por un camino real.

## What Changes

- Activa la pestaña "Bloques de ejercicios" de la cabecera del tech lead (hasta ahora un placeholder deshabilitado "Próximamente").
- Pantalla 5 "Bloques de ejercicios": listado de bloques activos (nombre, número de ejercicios, alumnos asignados, acceso al detalle) y, aparte, los bloques eliminados en solo lectura.
- Pantalla 6 "Nuevo/editar bloque de ejercicios": un único formulario sirve para crear y editar un bloque (nombre + selección de ejercicios guardados, filtrable por tipo y buscable por texto), reutilizando `POST /blocks` y `PATCH /blocks/{id}` ya existentes.
- Pantalla 7 "Detalle del bloque y asignación": editar (si el bloque no está resuelto) o eliminar el bloque; progreso detallado por alumno asignado, con la respuesta, el veredicto y la justificación de cada ejercicio de su copia; formulario para asignarlo a más alumnos.
- Pantalla 7b "Bloque eliminado": la misma vista de detalle en solo lectura completa, sin editar/eliminar/asignar, para un bloque ya eliminado.
- Ajustes de backend necesarios para que esas pantallas tengan los datos que el diseño pide (detectados revisando los esquemas reales, no asumidos a ciegas):
  - `GET /blocks` incluye un resumen de los alumnos asignados a cada bloque (columna de la pantalla 5).
  - `GET /blocks` y `GET /blocks/{id}` indican si el bloque esta resuelto (alguna de sus asignaciones tiene al menos una respuesta registrada), para deshabilitar "Editar bloque" en la pantalla 7 y mostrar el aviso "Resuelto · no editable" en la pantalla 5.
  - `GET /blocks/{id}` indica, por cada ejercicio de la composición, si está eliminado de la app (para que la pantalla 6, al editar, lo marque y bloquee el guardado hasta que se quite).
  - `GET /exercises` (capacidad `exercise-catalog`, ya existente) incluye en cuántos bloques está cada ejercicio guardado (selector de la pantalla 6).
  - `GET /blocks/{id}/assignments` incluye, por cada ejercicio de la copia de cada alumno, su tipo y enunciado, y, si está respondido, el texto de la respuesta y la justificación de la valoración -- no solo el veredicto (detalle expandible de la pantalla 7).

## Capabilities

### New Capabilities

(ninguna: las cuatro pantallas se apoyan en capacidades de backend ya existentes)

### Modified Capabilities

- `exercise-blocks`: el requisito "Listar y ver el detalle de un bloque" pasa a incluir, en el listado, un resumen de los alumnos asignados a cada bloque y si esta resuelto, y en el detalle, si cada ejercicio de la composición está eliminado de la app y si el bloque esta resuelto.
- `block-assignment`: el requisito "Consultar el progreso de un bloque asignado" pasa a incluir, por cada ejercicio de la copia del alumno, su tipo y enunciado, y, si está respondido, el texto de la respuesta y la justificación, no solo el veredicto.
- `exercise-catalog`: el requisito "Listar y buscar ejercicios definitivos" pasa a incluir, para cada ejercicio, en cuántos bloques está actualmente.

## Impact

- Backend: `backend/app/schemas/block.py` y `backend/app/routers/blocks.py` (resumen de alumnos y flag de resuelto en `BlockSummary`, flag de eliminado y de resuelto en el detalle, ampliación de `ExerciseProgress`/`StudentProgress`); `backend/app/schemas/exercise.py` y `backend/app/routers/exercises.py` (conteo de bloques en `SavedExerciseListItem`).
- Frontend: nuevo `frontend/src/app/core/blocks-api.model.ts` / `.service.ts`; nuevos componentes standalone bajo `frontend/src/app/tech-lead/` para las 4 pantallas; se activa la pestaña "Bloques de ejercicios" en `tech-lead-nav`; nuevas rutas guardadas por el `techLeadGuard` ya existente.
- Sin cambios de base de datos (las columnas y relaciones ya existen; solo se exponen más en las respuestas de los endpoints ya construidos). Sin CI/CD.
