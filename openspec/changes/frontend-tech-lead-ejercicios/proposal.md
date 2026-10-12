# Proposal

## Why

El tech lead ya puede generar ejercicios y guardarlos por backend (paso 2 del plan de trabajo), pero no tiene ninguna pantalla para hacerlo: el unico sitio post-login es un placeholder comun a los dos roles. Esta es la primera de las tres partes en que se ha dividido el paso 5 (frontend del tech lead): el area de "Ejercicios guardados" (pantallas 2, 3 y 4). Las otras dos (bloques; alumnos) son changes separados posteriores.

## What Changes

- Pantalla "Ejercicios guardados" (2): generaciones pendientes (Generando/Por revisar/Error) y tabla de ejercicios guardados con tipo, tecnologias y repositorio, con filtro por tipo y busqueda por texto. Boton "Generar ejercicios" y boton Eliminar en cada ejercicio.
- Pantalla "Generar ejercicios" (3): formulario con tecnologias (obligatorias), tipo de ejercicio y numero de candidatos (1 a 5). Sin campo de repositorio en esta primera parte (ver mas abajo) -- solo generacion basada en tecnologias.
- Pantalla "Revisar generacion" (4): ejercicios candidatos de una generacion en Ready, con su respuesta esperada editable y una casilla cada uno; boton "Guardar ejercicios" que guarda los candidatos marcados y cierra la revision de esa generacion.
- Cabecera con las tres pestanas del tech lead (Ejercicios guardados / Bloques de ejercicios / Alumnos, seccion 10): en este change solo "Ejercicios guardados" esta activa, las otras dos se muestran deshabilitadas ("Proximamente") hasta que lleguen sus propios changes.
- Un tech lead autenticado pasa a aterrizar en "Ejercicios guardados" en vez del home-placeholder actual.
- **Ajustes necesarios de backend** (sin ellos la pantalla 2 no puede funcionar): `GET /generations` no existe -- solo se puede crear una generacion y consultarla por id, no listar las pendientes. Se anade este endpoint. Ademas, el estado `done` ya existe en la base de datos (migracion `0001_schema.sql`) pero ningun codigo lo usa -- una generacion revisada se quedaria para siempre como "pendiente". Se anade la transicion a `done` al guardar los ejercicios de la revision (pantalla 4), y `GET /generations` deja de devolver las generaciones en `done`.

**Tercer ajuste necesario de backend:** `POST /exercises/{id}/save` no acepta ningun cuerpo -- solo marca `saved = true`. La pantalla 4 permite editar la respuesta esperada de un candidato antes de guardarlo ("con su respuesta esperada en un cuadro de texto editable"); como un candidato no guardado todavia no es inmutable, se anade un campo opcional para la respuesta esperada editada en ese mismo endpoint.

**Cuarto ajuste necesario de backend (detectado al implementar, no en la propuesta original):** la tabla de ejercicios guardados de la pantalla 2 muestra tecnologias y repositorio de cada ejercicio "via su generation" (seccion 10), pero `GET /exercises` solo devuelve campos propios del ejercicio (sin `generation_id`), y `GET /generations` ni siquiera incluiria la generacion si ya esta `done` -- que es justo el caso normal una vez sus candidatos se han guardado y la revision se ha cerrado. Se amplia `GET /exercises` para que incluya `technologies` y `repo_path` de la generacion de cada ejercicio (union con `generation`, sin filtrar por su estado).

**Fuera de alcance de esta primera parte, explicitamente decidido con el usuario:** subir un repositorio por ZIP o indicar una URL de GitHub (pantalla 3 de la especificacion). El backend no tiene ningun soporte para ello (`POST /generations` solo acepta `repo_path` como una ruta ya preparada en disco; no hay extraccion de ZIP ni clonado de GitHub en ningun sitio del codigo), y construirlo es trabajo de backend sustancial, no un ajuste de forma como los de arriba. Por tanto esta parte solo genera ejercicios sin repositorio (tipo `knowledge`); los tipos `debug`/`both`, que la especificacion liga a tener repositorio, quedan sin exponer en el formulario hasta que exista ese soporte en un change de backend aparte.

## Capabilities

### Modified Capabilities

- `exercise-generation`: se anade el requisito de poder listar las generaciones pendientes (`GET /generations`), y la transicion de una generacion de `ready` a `done` al cerrar su revision, dejando de aparecer en ese listado.
- `exercise-catalog`: el requisito "Guardar un ejercicio candidato como definitivo" se precisa para permitir editar la respuesta esperada del candidato en el mismo momento de guardarlo. El requisito "Listar y buscar ejercicios definitivos" se precisa para incluir las tecnologias y el repositorio de la generacion de cada ejercicio.

## Impact

- Backend: `backend/app/routers/generations.py` (nuevo `GET /generations`, nueva operacion para cerrar la revision), `backend/app/schemas/generation.py` (`GenerationStatus` admite `done`), `backend/app/routers/exercises.py` y `backend/app/schemas/exercise.py` (`POST /exercises/{id}/save` acepta una respuesta esperada editada opcional; `GET /exercises` incluye `technologies` y `repo_path` de la generacion de cada ejercicio).
- Frontend: nuevos componentes bajo `frontend/src/app/tech-lead/` (o carpeta equivalente) para las pantallas 2, 3 y 4, nuevo cliente HTTP para generaciones/ejercicios en `frontend/src/app/core/`, nuevo `techLeadGuard`, cambios en `app.routes.ts` y en `home-redirect.guard.ts` (el tech lead deja de quedarse en el home-placeholder).
- Fuera de alcance: subida de repositorio (ZIP/URL de GitHub) en backend y frontend; bloques y asignaciones (pantallas 5, 6, 7, 7b; siguiente change); alumnos (pantallas 5b, 5c; tercer change); CI/CD y despliegue (paso 6); cualquier otro requisito de `exercise-catalog`, `block-assignment`, `answer-evaluation` o `data-authorization`.
