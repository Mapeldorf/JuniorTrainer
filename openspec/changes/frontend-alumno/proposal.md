# Proposal

## Why

El alumno ya puede ser invitado, tiene bloques asignados y sus respuestas ya se evaluan (pasos 1-3 del plan de trabajo), pero no tiene ninguna pantalla para verlo: solo existe un placeholder post-login (`home`) comun a los dos roles. Sin esto, nadie puede usar la aplicacion como alumno.

## What Changes

- Pantalla "Mis bloques de ejercicios" (8): lista de asignaciones propias separadas en pendientes y hechas, con acceso a continuar o consultar.
- Pantalla "Ejercicio" (9): enunciado, codigo en solo lectura, respuesta y envio, con navegacion por el orden del bloque (barra de pasos o selector si hay mas de 10 ejercicios) y proteccion anti-copia en el enunciado y el cuadro de respuesta.
- Pantalla "Valoracion" (10): el mismo ejercicio ya respondido, en solo lectura, con el verdict y la justificacion, y navegacion Anterior/Siguiente sin pasar del siguiente pendiente.
- Cliente HTTP del frontend hacia FastAPI (no existia: hasta ahora el frontend solo hablaba con Supabase Auth), con el JWT de Supabase en la cabecera `Authorization`.
- **Ajuste necesario de backend** (no es una pantalla, pero sin el las pantallas 9 y 10 no pueden funcionar): `GET /assignments/{id}` no devuelve, para un ejercicio ya respondido, el texto de la respuesta del alumno ni el verdict ni la justificacion -- solo un booleano `answered`. Tampoco deja de incluir los ejercicios posteriores al primero sin responder, pese a que la especificacion (secciones 3 y 9) exige que el alumno no vea ni reciba esos ejercicios. Se corrige el shape de esta respuesta para alumno.
- **Segundo ajuste necesario de backend**, mismo motivo: `GET /assignments` no devuelve ningun progreso (ni conteo de ejercicios respondidos ni total), pese a que la seccion 9 de la especificacion lo exige ("Sus bloques asignados, con progreso") y la pantalla 8 lo necesita para separar pendientes de hechos y para distinguir "Empezar" de "Continuar".
- El home actual deja de ser el destino post-login para un alumno: a partir de este cambio, un alumno autenticado va a "Mis bloques de ejercicios"; un tech lead sigue cayendo en el home-placeholder hasta el paso 5.

## Capabilities

### New Capabilities

(ninguna: las pantallas son la implementacion de capacidades de alumno ya especificadas; no introducen comportamiento de sistema nuevo mas alla del ajuste de forma de respuesta que cubre la seccion siguiente. La proteccion anti-copia y la navegacion por pasos son decisiones de interfaz -- se documentan en design.md, no como requisito, porque son medidas "hasta donde el navegador lo permita", no verificables por el backend)

### Modified Capabilities

- `student-assignments`: el requisito "Ver el detalle de una asignacion propia" se precisa para que, al alumno, la respuesta incluya el texto de su respuesta, el verdict y la justificacion de cada ejercicio ya respondido, y nunca incluya ejercicios posteriores al primero sin responder.
- `student-assignments`: el requisito "Listar las propias asignaciones" se precisa para que cada asignacion incluya cuantos de sus ejercicios tienen ya respuesta y cuantos tiene en total.

## Impact

- Backend: `backend/app/schemas/assignment.py` (`AssignmentExerciseItem`), `backend/app/routers/assignments.py` (`get_my_assignment_detail`) -- solo la vista de alumno; no afecta a `answer_exercise` ni a los requisitos de `answer-evaluation`.
- Frontend: nuevo cliente HTTP (`frontend/src/app/core/`), tres componentes nuevos bajo `frontend/src/app/student/` (o carpeta equivalente), nuevas rutas guardadas por rol, y cambios en `app.routes.ts`/`app.config.ts` y en el destino post-login de `login.ts`. El `home` placeholder queda solo para tech lead hasta el paso 5.
- Fuera de alcance: frontend del tech lead (pantallas 2-7, 5b, 5c; paso 5), CI/CD y despliegue (paso 6), y cualquier otro endpoint o requisito de `answer-evaluation`, `block-assignment` o `data-authorization`.
