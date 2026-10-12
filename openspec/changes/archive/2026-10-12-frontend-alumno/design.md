# Design

## Context

Ver `proposal.md` - Why. El frontend (`frontend/src/app/`) solo tiene hoy las pantallas de autenticacion (`auth/login`, `auth/forgot`, `auth/set-password`) y un placeholder post-login comun a los dos roles (`home/`), con `SupabaseService` (solo Supabase Auth: login, logout, recuperacion, alta de contrasena) y `authGuard` (exige sesion, sin mirar el rol). No existe todavia ningun cliente HTTP hacia FastAPI: `environment.apiUrl` esta declarado pero sin usar.

El backend ya expone `GET /assignments`, `GET /assignments/{id}` y `POST /assignments/{assignment_id}/exercises/{exercise_id}/answer` (`backend/app/routers/assignments.py`), pero `GET /assignments/{id}` devuelve siempre todos los ejercicios de la copia (sin cortar en el primero sin responder) y, para los ya respondidos, solo un booleano `answered` -- sin el texto de la respuesta, el verdict ni la justificacion. Ver `proposal.md` - Modified Capabilities para el ajuste de `student-assignments` que esto exige. `GET /assignments` tiene el mismo problema de fondo: no devuelve ningun progreso, aunque la seccion 9 de la especificacion lo exige ("con progreso"). El mismo patron de conteo ya existe para el tech lead en `get_block_progress` (`backend/app/routers/blocks.py`, capacidad `block-assignment`): leer `assignment_exercise` y `answer` por `assignment_id` y comparar tamanos; aqui se aplica la misma idea para la lista del propio alumno, sin el cruce por `profile` que alli hace falta para el nombre del alumno.

## Goals / Non-Goals

**Goals:**
- Un alumno autenticado llega a "Mis bloques de ejercicios" y puede completar un bloque de principio a fin usando solo estas tres pantallas y los tres endpoints ya existentes (mas el ajuste de shape).
- Un unico cliente HTTP reutilizable para FastAPI, con el JWT de Supabase adjunto automaticamente, en el mismo sitio (`core/`) donde ya vive `SupabaseService`.
- El ajuste de `GET /assignments/{id}` es minimo: mismo endpoint, mismo esquema de entrada, solo cambia que campos devuelve y cuantos ejercicios incluye para un alumno.

**Non-Goals:**
- Frontend del tech lead y su propio guard de rol mas alla de lo estrictamente necesario para no romper su acceso actual al placeholder (paso 5).
- Resaltado de sintaxis en el codigo de solo lectura: se muestra en monospace plano: no lo pide ninguna pantalla y se puede anadir despues sin tocar la spec.
- Paginacion de "Mis bloques de ejercicios": el volumen esperado (bloques de un bootcamp) no la justifica todavia.
- Cualquier mitigacion adicional contra copiar/pegar mas alla de deshabilitar los eventos del navegador (la propia especificacion limita esto a "hasta donde el navegador lo permita").

## Decisions

**Un unico componente de ruta implementa las pantallas 9 y 10, no dos.** Ambas comparten enunciado, codigo, barra de pasos y la posicion en el bloque; la diferencia es si el ejercicio en esa posicion ya tiene respuesta (10: solo lectura, con verdict y justificacion) o todavia no (9: editable, con envio). Alternativa descartada: dos rutas/componentes distintos que navegan entre si tras enviar. Se descarta porque obligaria a duplicar la barra de pasos y la carga de datos en los dos componentes, para distinguir algo que ya es un dato del ejercicio (`answered`, y ahora tambien `verdict`/`justification`/`answer_text`), no un paso de navegacion distinto.

**Ruta por posicion dentro de la asignacion, no por `exercise_id`.** `/mis-bloques/:assignmentId/ejercicios/:position` (posicion 1-based, la misma que ya usa `AssignmentExerciseItem.position`). Alternativa descartada: rutear por `exercise_id`. Se descarta porque "anterior/siguiente" y los limites de navegacion (no pasar del primero sin responder) son aritmetica sobre la posicion, no busquedas por id; la posicion tambien es mas legible si el alumno comparte o recarga la URL.

**Tras enviar una respuesta, se vuelve a pedir `GET /assignments/{id}` en vez de actualizar el estado local a mano.** Alternativa descartada: anadir localmente el `AnswerResult` que devuelve el POST al ejercicio recien respondido y mantener el resto del estado como estaba. Se descarta porque el alumno pasa a tener un nuevo ejercicio siguiente "desbloqueado" cuyo enunciado y codigo el frontend todavia no tiene en memoria -- el backend es quien decide que se ve ahora, asi que se le vuelve a preguntar. El volumen (hasta 100 ejercicios por asignacion) hace que este round-trip extra sea intrascendente.

**El destino post-login por rol se decide en un guard de la ruta raiz, no en `login.ts`.** Se anade `homeRedirectGuard` en `core/`, aplicado a la ruta `''`: si el rol es `student`, devuelve `UrlTree(['/mis-bloques'])` (mismo patron que ya usa `authGuard`, que devuelve un `UrlTree` a `/login` sin sesion); si es `tech_lead`, deja pasar al `home` placeholder actual. `login.ts` no cambia su `navigate(['/'])`: el guard decide. Alternativa descartada: que `login.ts` lea el rol y navegue directamente a `/mis-bloques` o `/`. Se descarta porque duplicaria la misma decision de rol en dos sitios (login y cualquier otra entrada a `/`, como abrir la URL raiz con una sesion ya iniciada).

**Nuevo `studentGuard` en `core/`, junto a `authGuard`, para las rutas de alumno.** Sigue el mismo patron (`CanActivateFn`, lee el rol de `SupabaseService.getRole()`, `UrlTree` si no cuadra) en vez de meter la comprobacion de rol dentro de cada componente. Un tech lead que entre a `/mis-bloques` a mano se redirige a `/` (mismo criterio que el 403 ya establecido en backend para rutas cruzadas de rol, aunque aqui no hay nada que proteger salvo la UX: el backend ya exige `require_student` en los tres endpoints).

**El progreso de `GET /assignments` se calcula con dos conteos por asignacion, no con una subconsulta por fila.** `list_my_assignments` pasa de un solo `select` sobre `assignment` a tres lecturas: las asignaciones del alumno, el numero de `assignment_exercise` por `assignment_id` (`total_count`) y el numero de `answer` por `assignment_id` (`answered_count`), cruzadas en Python igual que ya hace `get_block_progress`. Alternativa descartada: una vista SQL o una funcion Postgres que devuelva el conteo ya hecho. Se descarta por el mismo motivo que `design.md` de `bloques-asignaciones` ya dio para no usar RPC: el volumen (asignaciones de un alumno) es bajo y el proyecto no usa ese patron todavia.

**Un servicio `AssignmentsApiService` en `core/`, no una llamada `fetch` o `HttpClient` directa desde cada componente.** Envuelve los tres endpoints (`listMine`, `getDetail`, `submitAnswer`) devolviendo los tipos ya definidos en el backend (se replican como interfaces TypeScript, sin generador de cliente: el proyecto no tiene OpenAPI-codegen y los tres endpoints son pocos y estables). El JWT se adjunta con un `HttpInterceptorFn` (`authInterceptor`) registrado una vez en `app.config.ts` via `provideHttpClient(withInterceptors([authInterceptor]))`, que antepone `Authorization: Bearer <access_token>` a toda peticion cuyo `url` empiece por `environment.apiUrl` -- no a las peticiones que el SDK de Supabase hace por su cuenta.

**Proteccion anti-copia como una directiva de atributo reutilizable, no codigo repetido en cada plantilla.** `NoCopyPasteDirective` (`core/` o `shared/`) escucha `copy`, `cut`, `paste`, `dragstart` y `contextmenu` con `event.preventDefault()`, aplicada al bloque del enunciado/codigo y al `textarea` de respuesta. Mismo hueco que ya reconoce la especificacion: no cubre capturas de pantalla ni DevTools, solo los gestos de navegador que el documento pide bloquear.

**Barra de pasos vs. selector es un umbral local (`exercises.length > 10`), sin pedir nada nuevo al backend.** El propio detalle de la asignacion ya trae todos los ejercicios visibles (hasta el primero sin responder); el componente decide la variante de navegacion con ese mismo array.

## Risks / Trade-offs

[Riesgo] Cambiar el shape de `GET /assignments/{id}` para alumno es un cambio de contrato de API → Mitigacion: no existe hoy ningun consumidor de ese endpoint (este change es el primero que lo llama desde un cliente); la vista del tech lead sobre las respuestas de un alumno pasa por `GET /blocks/{id}`, un endpoint distinto, sin tocar.

[Riesgo] Volver a pedir el detalle completo tras cada respuesta repite datos ya conocidos (ejercicios anteriores ya respondidos) → Mitigacion: el limite de 100 ejercicios por asignacion mantiene la respuesta pequena; no hay indicio de que esto sea un problema de rendimiento a la escala de un bootcamp.

[Riesgo] La proteccion anti-copia es evitable (DevTools, extensiones, capturar pantalla) → Mitigacion: ninguna adicional; la propia especificacion acota esto a "hasta donde el navegador lo permita" y no lo trata como una garantia de seguridad, solo como friccion deliberada.

[Riesgo] Enrutar por `position` en vez de por `exercise_id` podria desincronizarse si dos pestanas del mismo alumno envian respuestas a la vez → Mitigacion: el backend ya rechaza con 409 una segunda respuesta al mismo ejercicio (`answer-evaluation` - "Un ejercicio de una asignacion solo se responde una vez"); el frontend solo necesita volver a pedir el detalle si recibe ese 409 para resincronizar su barra de pasos, no hace falta ningun bloqueo adicional en el cliente.
