# Tasks

## 1. Ajuste de backend: listado, cierre de revision y respuesta editada (exercise-generation, exercise-catalog)

- [x] 1.1 `backend/app/schemas/generation.py`: `GenerationStatus` admite `done`; nuevo `GenerationSummary` (sin `candidates`, para el listado) si `GenerationStatusResponse` no encaja tal cual
- [x] 1.2 `backend/app/routers/generations.py`: nuevo `GET /generations` (tech lead) que devuelve las generaciones con `status != 'done'`, ordenadas por `created_at desc`; verificar con un test o script que una generacion `done` no aparece y las demas si
- [x] 1.3 `backend/app/routers/generations.py`: nuevo `POST /generations/{id}/close` (tech lead, solo desde `ready`) que pasa la generacion a `done`; verificar con un test o script que cerrar una `ready` funciona (incluso con candidatos sin guardar), que cerrar una `generating` o `error` se rechaza, y que tras cerrarla ya no aparece en `GET /generations`
- [x] 1.4 `backend/app/schemas/exercise.py` y `backend/app/routers/exercises.py`: `POST /exercises/{id}/save` acepta un body opcional con `expected_answer`; si viene, se guarda esa respuesta esperada en vez de la original; verificar con un test o script ambos casos (con y sin `expected_answer` en el body)
- [x] 1.5 `backend/app/schemas/exercise.py` y `backend/app/routers/exercises.py`: `GET /exercises` incluye `technologies` y `repo_path` de la generacion de cada ejercicio (union por `generation_id`, sin filtrar por el estado de esa generacion -- design.md decision 9); verificar con un test o script que aparecen correctamente, incluso para un ejercicio cuya generacion ya esta `done`
- [x] 1.6 Verificar en vivo contra el backend real (extender `backend/scripts/verify_generation_e2e.py` o escribir un script nuevo equivalente) el flujo completo: generar sin repositorio, listar pendientes, revisar y guardar con una respuesta editada, cerrar la revision, confirmar que desaparece de pendientes, y que el ejercicio guardado aparece en `GET /exercises` con las tecnologias y el repositorio de esa generacion; limpiar los datos de prueba al terminar

## 2. Cliente HTTP y guard de rol

- [x] 2.1 Tipos TS de los DTOs de `GET /generations`, `POST /generations`, `GET /generations/{id}`, `POST /generations/{id}/close`, `GET /exercises`, `POST /exercises/{id}/save` y `PATCH /exercises/{id}` en `frontend/src/app/core/generations-api.model.ts`; verificar que `npx tsc --noEmit` compila sin errores
- [x] 2.2 `GenerationsApiService` en `frontend/src/app/core/generations-api.service.ts` con `listPending()`, `start(...)`, `getDetail(id)`, `close(id)`, `listSaved(filters)`, `save(exerciseId, expectedAnswer?)`, `delete(exerciseId)`; reutiliza `authInterceptor` ya existente; verificar con `provideHttpClientTesting` que cada metodo llama al endpoint, metodo HTTP y URL correctos
- [x] 2.3 `techLeadGuard` en `frontend/src/app/core/tech-lead.guard.ts` (mismo patron que `studentGuard`: exige rol `tech_lead`, sin sesion a login, con sesion sin ese rol a `/`); verificar con tests los casos tech_lead/student/sin sesion
- [x] 2.4 Actualizar `homeRedirectGuard` para mandar a un tech lead a `/ejercicios` (no quedarse en `/`); verificar con un test que un tech lead autenticado se redirige y un alumno sigue yendo a `/mis-bloques`

## 3. Cabecera de navegacion del tech lead

- [x] 3.1 Componente standalone `frontend/src/app/tech-lead/tech-lead-nav/tech-lead-nav.ts` + `.html`: tres pestanas (Ejercicios guardados / Bloques de ejercicios / Alumnos), solo la primera activa y enlazada a `/ejercicios`, las otras dos deshabilitadas con indicacion "Proximamente"; verificar con un test que las dos deshabilitadas no son clicables (sin `routerLink` o con `aria-disabled`)

## 4. Pantalla "Ejercicios guardados" (2)

- [x] 4.1 Componente standalone `frontend/src/app/tech-lead/ejercicios/ejercicios.ts` + `.html`: incluye `TechLeadNavComponent`; carga `GenerationsApiService.listPending()` y `listSaved()`; tabla de ejercicios guardados con tipo, tecnologias (via su `generation`) y repositorio, filtro por tipo y busqueda por texto (parametros de `listSaved`)
- [x] 4.2 Lista de generaciones pendientes con su estado (Generando/Por revisar/Error); polling cada 3s de `listPending()` mientras haya alguna `generating` (design.md - Decisions), deteniendolo cuando no quede ninguna; verificar con un test (fake timers) que el polling se detiene cuando ya no hay generaciones en curso
- [x] 4.3 Boton "Generar ejercicios" (navega a `/ejercicios/generar`) y boton Eliminar en cada ejercicio guardado (`GenerationsApiService.delete`, con confirmacion); verificar con un test que eliminar llama al endpoint y refresca la lista
- [x] 4.4 Registrar la ruta `ejercicios` (guardada por `authGuard` + `techLeadGuard`) en `app.routes.ts`; verificar con `npx vitest run` que el componente renderiza generaciones pendientes y ejercicios guardados a partir de datos de prueba, y que el filtro/busqueda funcionan

## 5. Pantalla "Generar ejercicios" (3)

- [x] 5.1 Componente standalone `frontend/src/app/tech-lead/generar/generar.ts` + `.html`: formulario con tecnologias (obligatorio, lista editable) y numero de candidatos (1 a 5); sin campo de repositorio ni selector de tipo (design.md - Decisions "Goals/Non-Goals"), toda generacion de este formulario es `knowledge`
- [x] 5.2 Boton Generar llama a `GenerationsApiService.start(...)` y navega de vuelta a `/ejercicios`, donde la nueva generacion aparece como "Generando" (via el polling de la tarea 4.2); verificar con un test que el formulario no se puede enviar sin tecnologias ni con un numero fuera de 1-5, y que al enviarlo con datos validos se llama al endpoint y se navega
- [x] 5.3 Registrar la ruta `ejercicios/generar` (guardada por `authGuard` + `techLeadGuard`) en `app.routes.ts`; verificar con `npx vitest run`

## 6. Pantalla "Revisar generacion" (4)

- [x] 6.1 Componente standalone `frontend/src/app/tech-lead/revisar/revisar.ts` + `.html`: lee el id de generacion de la ruta, pide `GenerationsApiService.getDetail(id)` y muestra sus candidatos (enunciado, codigo en solo lectura, respuesta esperada en un cuadro de texto editable, y una casilla); si la generacion no esta `ready` (en curso o en error), muestra ese estado en vez de la lista de candidatos
- [x] 6.2 Boton "Guardar ejercicios": llama a `GenerationsApiService.save(...)` por cada candidato marcado (con su respuesta esperada editada si cambio) y despues a `close(id)` (design.md - Decisions), y navega de vuelta a `/ejercicios`; verificar con un test que guarda solo los marcados, con la respuesta esperada que corresponda, cierra la generacion, y funciona igual con 0 candidatos marcados
- [x] 6.3 Registrar la ruta `ejercicios/:generationId/revisar` (guardada por `authGuard` + `techLeadGuard`) en `app.routes.ts`; verificar con `npx vitest run` el componente en los tres estados de una generacion (en curso, lista para revisar, en error)

## 7. Verificacion de extremo a extremo

- [x] 7.1 Pedir al usuario que ejecute `ng serve` (frontend) junto al backend real y los 3 agentes de generacion (web, codigo, ejercicios) y haga, como tech lead, el flujo completo: entrar y llegar a "Ejercicios guardados", generar sin repositorio, verla pasar de "Generando" a "Por revisar", revisarla editando una respuesta esperada y guardando solo algunos candidatos, confirmar que la generacion desaparece de pendientes y los guardados aparecen en la tabla, y eliminar uno
- [x] 7.2 Pedir al usuario que confirme, en esa misma sesion, que un alumno que visita `/` sigue yendo a "Mis bloques de ejercicios" (no se ve afectado por el cambio del redireccionamiento del tech lead)
- [x] 7.3 Ejecutar `npx vitest run` (frontend) y confirmar que toda la suite pasa, y ejecutar la suite de tests de backend existente (si la hay) para confirmar que los ajustes del grupo 1 no rompen nada ya cubierto

## Workflow follow-up

- Abrir una rama `change/frontend-tech-lead-ejercicios` (ya creada) y un PR hacia `develop` cuando los grupos 1-7 esten completos y verificados.
- Archivar el change (sincronizando los deltas de `exercise-generation` y `exercise-catalog` en sus specs existentes) una vez el PR este aprobado.
