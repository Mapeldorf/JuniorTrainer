# Tasks

## 1. Ajuste de backend: progreso y detalle para el alumno (student-assignments)

- [x] 1.1 `backend/app/schemas/assignment.py`: ampliar `AssignmentSummary` con `answered_count` y `total_count`; ampliar `AssignmentExerciseItem` con `answer_text`, `verdict` y `justification` (opcionales, solo presentes si `answered`)
- [x] 1.2 `backend/app/routers/assignments.py`: `list_my_assignments` calcula `answered_count`/`total_count` por asignacion (mismo patron de conteo que `get_block_progress` en `blocks.py`, segun `design.md` - Decisions); verificar con un test o script que una asignacion sin respuestas da `answered_count = 0` y una con todas sus respuestas da `answered_count == total_count`
- [x] 1.3 `backend/app/routers/assignments.py`: `get_my_assignment_detail` deja de incluir ejercicios posteriores al primero sin responder, y rellena `answer_text`/`verdict`/`justification` para los ya respondidos leyendo `answer`; verificar con un test o script que una asignacion con un ejercicio respondido, uno sin responder y uno mas alla solo devuelve los dos primeros, y que el respondido incluye su texto, verdict y justificacion
- [x] 1.4 Verificar en vivo contra el backend real y una asignacion de prueba (extender `backend/scripts/verify_valoracion_respuestas.py` o escribir un script nuevo equivalente) que `GET /assignments` informa el progreso correcto y que `GET /assignments/{id}` corta en el primer ejercicio sin responder y expone el detalle de los ya respondidos; limpiar los datos de prueba al terminar

## 2. Cliente HTTP y guards de rol

- [x] 2.1 Tipos TS de los DTOs de `GET /assignments`, `GET /assignments/{id}` y `POST .../answer` (con los campos de la tarea 1.1) en `frontend/src/app/core/assignments-api.model.ts`; verificar que `npx tsc --noEmit` compila sin errores
- [x] 2.2 `authInterceptor` (`HttpInterceptorFn`) en `frontend/src/app/core/auth.interceptor.ts`, que antepone `Authorization: Bearer <access_token>` solo a peticiones cuyo `url` empiece por `environment.apiUrl`, leyendo la sesion de `SupabaseService`; registrarlo con `provideHttpClient(withInterceptors([authInterceptor]))` en `app.config.ts`; verificar con un test (`vitest`) que una peticion a `environment.apiUrl` lleva la cabecera y una peticion a otra URL no
- [x] 2.3 `AssignmentsApiService` en `frontend/src/app/core/assignments-api.service.ts` con `listMine()`, `getDetail(assignmentId)` y `submitAnswer(assignmentId, exerciseId, text)`; verificar con `provideHttpClientTesting` que cada metodo llama al endpoint, metodo HTTP y URL correctos y devuelve el tipo esperado
- [x] 2.4 `studentGuard` en `frontend/src/app/core/student.guard.ts` (deniega y redirige a `/` si el rol no es `student`) y `homeRedirectGuard` en `frontend/src/app/core/home-redirect.guard.ts` (redirige a `/mis-bloques` si el rol es `student`, deja pasar si es `tech_lead`), junto a `auth.guard.ts`; verificar con tests los casos student/tech_lead/sin sesion de cada uno
- [x] 2.5 Aplicar `homeRedirectGuard` a la ruta `''` (ademas del `authGuard` ya existente) en `app.routes.ts`; verificar con un test de rutas o manualmente que un alumno autenticado que visita `/` termina en `/mis-bloques` y un tech lead se queda en el `home` actual

## 3. Pantalla "Mis bloques de ejercicios" (8)

- [x] 3.1 Componente standalone `frontend/src/app/student/mis-bloques/mis-bloques.ts` + `.html`: carga `AssignmentsApiService.listMine()` y separa en pendientes (`answered_count < total_count`) y hechos (`answered_count === total_count`), con boton "Empezar" (`answered_count === 0`) o "Continuar" (`0 < answered_count < total_count`) en los pendientes y "Consultar" en los hechos
- [x] 3.2 Boton "Empezar"/"Continuar" navega a `/mis-bloques/:assignmentId/ejercicios/:position`, con `position = answered_count + 1` (el siguiente sin responder); "Consultar" navega a la posicion 1 de esa misma ruta
- [x] 3.3 Registrar la ruta `mis-bloques` (guardada por `authGuard` + `studentGuard`) en `app.routes.ts`; verificar con `npx vitest run` que el componente renderiza las dos listas a partir de asignaciones de prueba con distintas combinaciones de `answered_count`/`total_count`

## 4. Pantalla "Ejercicio" / "Valoracion" (9 y 10)

- [x] 4.1 Directiva `NoCopyPasteDirective` en `frontend/src/app/core/no-copy-paste.directive.ts` que cancela `copy`, `cut`, `paste`, `dragstart` y `contextmenu`; verificar con un test que disparar esos eventos sobre un elemento con la directiva no deja pasar el valor por defecto (`event.defaultPrevented`)
- [x] 4.2 Componente standalone `frontend/src/app/student/ejercicio/ejercicio.ts` + `.html`: lee `assignmentId`/`position` de la ruta, pide `AssignmentsApiService.getDetail(assignmentId)` y resuelve el ejercicio en esa posicion; aplica `NoCopyPasteDirective` al enunciado/codigo y al cuadro de respuesta
- [x] 4.3 Variante pantalla 9 (ejercicio sin responder en esa posicion): enunciado, codigo en solo lectura, `textarea` y boton Enviar que llama a `AssignmentsApiService.submitAnswer(...)` y, al terminar, vuelve a pedir el detalle (segun `design.md` - Decisions) para pasar a la variante de la tarea 4.4 sin navegar de pantalla
- [x] 4.4 Variante pantalla 10 (ejercicio ya respondido en esa posicion): mismo enunciado/codigo, respuesta bloqueada, `verdict` (traducido a Correcta/Incompleta/Incorrecta, seccion 5) y justificacion, botones Anterior/Siguiente que cambian `position` sin pasar del primero sin responder ni de 1
- [x] 4.5 Barra de pasos (hasta 10 ejercicios) o selector "Ir a un ejercicio respondido" (mas de 10, segun `design.md` - Decisions) que solo permite ir a posiciones ya visibles en el detalle (respondidas o la siguiente pendiente)
- [x] 4.6 Registrar la ruta `mis-bloques/:assignmentId/ejercicios/:position` (guardada por `authGuard` + `studentGuard`) en `app.routes.ts`; verificar con `npx vitest run` el componente con asignaciones de prueba en los tres estados: con ejercicios pendientes (9), con ejercicios respondidos (10) y completada (sin Siguiente mas alla del ultimo)
- [x] 4.7 Verificar con un test que enviar una respuesta a un ejercicio ya respondido (p. ej. tras un 409 del backend por una segunda pestana) no rompe el componente: vuelve a pedir el detalle y muestra la variante de solo lectura en vez de un error sin manejar

## 5. Verificacion de extremo a extremo

- [x] 5.1 Pedir al usuario que ejecute `ng serve` (frontend) junto al backend real (`docker compose up` o `uvicorn` local) y haga, con un alumno de prueba, el flujo completo descrito en `proposal.md`: entrar y llegar a "Mis bloques de ejercicios", empezar un bloque, responder un ejercicio y ver su valoracion al momento, navegar hacia atras a uno ya respondido en solo lectura, continuar hasta terminar el bloque y verlo pasar a "hechos", y confirmar que copiar/pegar/arrastrar/menu contextual no funcionan en el enunciado ni en la respuesta
- [x] 5.2 Pedir al usuario que confirme, en ese mismo flujo, que un tech lead que visita `/` sigue llegando al `home` actual (no se le redirige a "Mis bloques de ejercicios")
- [x] 5.3 Ejecutar `npx vitest run` (frontend) y confirmar que toda la suite pasa, y ejecutar la suite de tests de backend existente (si la hay) para confirmar que el ajuste del grupo 1 no rompe nada ya cubierto

## Workflow follow-up

- Abrir una rama `change/frontend-alumno` (ya creada) y un PR hacia `develop` cuando los grupos 1-5 esten completos y verificados.
- Archivar el change (sincronizando el delta de `student-assignments` en su spec existente) una vez el PR este aprobado.
