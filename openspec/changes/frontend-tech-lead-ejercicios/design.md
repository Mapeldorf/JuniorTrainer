# Design

## Context

Backend ya construido (paso 2 del plan): `POST /generations` dispara una generacion en segundo plano (agentes web/codigo/ejercicios por A2A) y responde de inmediato con el id; `GET /generations/{id}` consulta su estado (`generating`/`ready`/`error`) y, si esta `ready`, sus candidatos. `GET /exercises`, `POST /exercises/{id}/save` y `PATCH /exercises/{id}` (borrado logico) ya gestionan el catalogo de ejercicios definitivos. No existe listado de generaciones ni cierre de revision (ver proposal.md - Why).

Frontend ya tiene el patron de alumno (change `frontend-alumno`, archivado): componentes standalone con signals, cliente HTTP por `HttpClient` + `authInterceptor` (ya existente, reutilizable tal cual), guards funcionales por rol (`studentGuard`, `homeRedirectGuard`), rutas con `loadComponent` + `withComponentInputBinding`.

## Goals / Non-Goals

**Goals:**
- Pantallas 2, 3 y 4 funcionales contra el backend real (incluidos los 3 ajustes de backend descritos en la propuesta).
- Un tech lead autenticado aterriza en "Ejercicios guardados".

**Non-Goals:**
- Subida de repositorio (ZIP/URL de GitHub): fuera de alcance, decidido con el usuario (ver proposal.md).
- Pestanas "Bloques de ejercicios" y "Alumnos": solo se muestran deshabilitadas, su contenido real llega en los 2 changes siguientes.
- Edicion del enunciado o el codigo de un candidato: la especificacion solo menciona la respuesta esperada como editable (seccion 10, pantalla 4).

## Decisions

1. **Reflejar el progreso de una generacion con polling simple.** La generacion corre en segundo plano sin WebSocket ni SSE (`BackgroundTasks` de FastAPI, ver `orchestrator.py`), asi que el frontend no tiene forma de que el backend le avise cuando cambia de estado. Pantalla 2/3 hacen polling de `GET /generations` cada 3s mientras haya alguna generacion en estado `generating`, y lo detienen en cuanto ninguna lo esta. Alternativa descartada: SSE/WebSocket -- no existe en el backend y anadirlo es desproporcionado para una lista que cambia cada pocos segundos como mucho.

2. **`GET /generations` solo devuelve las no cerradas (`status != 'done'`), ordenadas por `created_at desc`.** Coincide exactamente con "generaciones pendientes" de la pantalla 2 (seccion 10); no hace falta un parametro de filtro porque no hay ningun caso de uso que necesite ver las `done`.

3. **Cerrar la revision es una operacion dedicada, no implicita en guardar un ejercicio.** `POST /generations/{id}/close` (solo tech lead, solo desde `ready`) se llama una vez al pulsar "Guardar ejercicios" en pantalla 4, despues de los `POST /exercises/{id}/save` de los candidatos marcados -- asi una generacion con 0 candidatos marcados tambien se puede cerrar (requisito "Cerrar la revision con candidatos sin guardar"). Alternativa descartada: cerrarla automaticamente al guardar el ultimo candidato visible -- mas implicito y no cubre el caso de cerrar sin guardar ninguno.

4. **La respuesta esperada editada viaja en el body de `POST /exercises/{id}/save`.** Campo opcional `expected_answer: str | None`; si se omite, se guarda la respuesta esperada ya generada (comportamiento actual sin cambios). Evita inventar un endpoint de edicion de candidatos que no tiene mas uso que este.

5. **Sin repositorio, el formulario de pantalla 3 solo ofrece tipo `knowledge`.** La especificacion liga `debug`/`both` a tener repositorio ("tipo (sin repositorio solo conocimiento)", seccion 10); como esta parte no tiene subida de repositorio, el selector de tipo ni siquiera se muestra -- toda generacion de este change es `knowledge`. El backend no impone esta restriccion a nivel de API (puede pedirse `debug` sin repo), asi que queda como validacion solo del frontend hasta que exista subida de repositorio.

6. **Cabecera de 3 pestanas con 2 deshabilitadas.** Para no construir una navegacion a medias con una sola pantalla suelta, se anade ya la cabecera de las 3 pestanas (seccion 10), con "Bloques de ejercicios" y "Alumnos" visualmente presentes pero no clicables ("Proximamente"), listas para activarse en los 2 changes siguientes sin tocar esta cabecera de nuevo.

7. **`techLeadGuard` nuevo, mismo patron que `studentGuard`.** Exige rol `tech_lead`; sin sesion manda a login, con sesion pero sin ese rol manda a `/`. `homeRedirectGuard` se actualiza para mandar a un tech lead a `/ejercicios` en vez de dejarlo en `/` (el `home` placeholder deja de usarse para tech lead).

8. **Cliente HTTP nuevo, `GenerationsApiService`, en vez de extender `AssignmentsApiService`.** Mismo patron (HttpClient + authInterceptor), pero capacidad distinta (generaciones/ejercicios vs asignaciones), igual que ya hay servicios separados por capacidad.

9. **`GET /exercises` incluye `technologies` y `repo_path` de la generacion de cada ejercicio, sin filtrar por el estado de esa generacion (detectado al implementar, no en la propuesta original).** Se expone con un esquema nuevo, `SavedExerciseListItem` (solo para este listado), en vez de anadir esos campos a `SavedExercise` -- `SavedExercise` lo sigue usando tambien `BlockExerciseItem` (detalle de un bloque, capacidad fuera de alcance de este change) con una consulta que no une con `generation`; ampliar `SavedExercise` directamente habria roto esa consulta. La pantalla 2 (seccion 10) muestra tecnologias y repositorio en la tabla de guardados "via su generation", pero `GET /generations` (decision 2) solo devuelve las no cerradas -- justo lo contrario del caso normal, donde la generacion ya se cerro al guardar sus candidatos. La unica forma de que la tabla de guardados muestre esos datos es que el propio `GET /exercises` los incluya, uniendo cada ejercicio con su `generation` (por `generation_id`) sin filtrar por `status`. Alternativa descartada: que el frontend junte el ejercicio con una llamada aparte a `GET /generations/{id}` -- ademas de forzar una llamada por ejercicio para una sola tabla, `GenerationStatusResponse` ni siquiera expone hoy `technologies`/`repo_path` (solo `id`, `status`, `error_message`, `candidates`), asi que tambien habria que ampliarlo ahi.

## Risks / Trade-offs

- [Polling cada 3s mientras hay una generacion en curso puede generar carga si varios tech leads tienen la pantalla abierta a la vez] → aceptable para el volumen esperado (equipo pequeno, generaciones ocasionales); si se vuelve un problema, pasar a SSE es un cambio de implementacion detras del mismo endpoint, no de contrato.
- [Cerrar la revision descarta sin aviso los candidatos no marcados, que quedan huerfanos (`saved=false` para siempre, invisibles salvo consultando la generacion por id)] → coincide con la decision explicita del usuario; no se borran de la base de datos, solo dejan de ser accesibles desde la pantalla 2.
- [La restriccion "sin repositorio solo conocimiento" solo vive en el frontend, no en el backend] → riesgo menor: el endpoint ya acepta `debug`/`both` sin repo porque nunca se penso usar asi; se documenta aqui para no sorprender a quien construya la subida de repositorio mas adelante.
