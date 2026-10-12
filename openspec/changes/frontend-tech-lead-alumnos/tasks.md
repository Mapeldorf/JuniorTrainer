# Tasks

## 1. Backend: progreso de un alumno a traves de sus bloques (block-assignment)

- [x] 1.1 `backend/app/schemas/block.py`: anadir `StudentBlockAssignment` (`assignment_id: str`, `block_id: str`, `block_name: str`, `exercises: list[ExerciseProgress]`), reusando `ExerciseProgress` ya existente
- [x] 1.2 `backend/app/routers/users.py`: anadir `_get_student_or_404(student_id)` (consulta `profile` por id y `role = student`; 404 si no existe o no es alumno) y `GET /users/{student_id}/blocks` (`require_tech_lead`), reusando el mismo patron de consultas batched de `get_block_progress` (`assignment`+`block`, `assignment_exercise`+`exercise`, `answer`) pero filtrado por `student_id` en vez de `block_id`, incluyendo asignaciones de bloques eliminados (design.md - decision D3), ordenadas por `assigned_at` ascendente; verificar con un test o script que un alumno con varios bloques (incluyendo uno eliminado) devuelve una entrada por asignacion con su `block_name` y el detalle por ejercicio, que un alumno sin asignaciones devuelve `[]`, que un alumno llamando a este endpoint recibe 403, y que un id que no es de un alumno existente recibe 404

## 2. Verificacion de backend contra la base real

- [x] 2.1 Ejecutar (o extender el script existente de verificacion de bloques) un flujo end-to-end contra el backend real: crear un alumno, asignarle dos bloques, responder un ejercicio de uno de ellos, eliminar ese bloque, y confirmar que `GET /users/{id}/blocks` sigue devolviendo ambas asignaciones (la del bloque eliminado incluida) con el `block_name` y el detalle por ejercicio correctos; limpiar los datos de prueba al terminar

## 3. Cliente HTTP de alumnos

- [x] 3.1 `frontend/src/app/core/users-api.model.ts`: anadir `InviteStudentRequest` (`name: string`, `email: string`) y `StudentBlockAssignment` (reusando `ExerciseProgress` de `blocks-api.model.ts`); verificar que `npx tsc --noEmit -p tsconfig.app.json` compila sin errores
- [x] 3.2 `frontend/src/app/core/users-api.service.ts`: anadir `invite(body: InviteStudentRequest)` (`POST /users`, deja propagarse el error HTTP sin envolverlo para que el componente distinga 409) y `getBlocks(studentId: string)` (`GET /users/{id}/blocks`); verificar con `provideHttpClientTesting` que ambos metodos llaman al endpoint, metodo HTTP y URL correctos, y que un 409 de `invite` llega al subscriber como error

## 4. Pantalla "Alumnos" (5b)

- [x] 4.1 Componente standalone `frontend/src/app/tech-lead/alumnos/alumnos.ts` + `.html`: incluye `TechLeadNavComponent`; formulario Nombre + Email + boton "Invitar alumno" (`UsersApiService.invite`); tras exito, banner verde "Invitacion enviada a `<email>`." y formulario vacio; si el error es 409, banner rojo "Ya existe un alumno con el email `<email>`." con el campo email marcado `aria-invalid` y sin perder lo escrito; cualquier otro error, banner generico; tabla "Alumnos (N)" (`UsersApiService.listStudents()`) con columnas Nombre/Email/Accion ("Ver detalle" -> `/alumnos/:studentId`)
- [x] 4.2 Registrar la ruta `alumnos` (guardada por `authGuard` + `techLeadGuard`) en `app.routes.ts`; activar el enlace "Alumnos" en `tech-lead-nav.ts`/`.html` (deja de estar "Proximamente"); verificar con un test que esa pestana ya es clicable
- [x] 4.3 Verificar con `npx ng test` el componente en sus tres casos (invitacion correcta, email duplicado con 409, error generico) y que la tabla renderiza los alumnos de prueba con su enlace a detalle

## 5. Pantalla "Detalle de un alumno" (5c)

- [x] 5.1 Componente standalone `frontend/src/app/tech-lead/alumno-detalle/alumno-detalle.ts` + `.html`: lee `studentId` de la ruta; enlace "Alumnos" para volver; resuelve nombre/email del alumno buscandolo en `UsersApiService.listStudents()` (design.md - decision D del no-goal, sin endpoint nuevo para un solo alumno); carga `UsersApiService.getBlocks(studentId)`; cabecera con nombre y "`<email>` · N bloques de ejercicios asignados"
- [x] 5.2 Seccion "Bloques de ejercicios asignados (N)": un desplegable por asignacion con resumen colapsado (nombre del bloque, badge de estado calculado -- "Sin empezar · 0 de N" / "En curso · X de N" / "Completado · N de N" -- y contadores de correctas/incompletas/incorrectas o "Sin respuestas"); al expandir, enlace "Ver detalle del bloque" (navega a `/bloques/:blockId`) y la lista ordenada de ejercicios de esa asignacion (numero, tipo, enunciado, y si esta respondido badge de verdict + respuesta + justificacion, o "Sin responder"); verificar con un test que el estado/contadores se calculan bien para los tres casos (sin empezar, en curso, completado) y que el detalle expandido muestra los datos de cada ejercicio
- [x] 5.3 Registrar la ruta `alumnos/:studentId` (guardada por `authGuard` + `techLeadGuard`) en `app.routes.ts`, y enlazar "Ver detalle" de la pantalla 5b a esta ruta; verificar con `npx ng test` el componente con un alumno con varios bloques, incluyendo uno sin ninguna respuesta todavia

## 6. Verificacion de extremo a extremo

- [x] 6.1 Pedir al usuario que ejecute `ng serve` (frontend) junto al backend real y haga, como tech lead, el flujo completo: invitar un alumno nuevo (banner de exito), intentar invitar el mismo email otra vez (banner de email duplicado), abrir el detalle de un alumno con varios bloques asignados, expandir cada uno y confirmar que el estado/contadores y el detalle por ejercicio coinciden con lo que ve en la pantalla 7, y comprobar que un bloque que se elimina despues de asignarlo sigue apareciendo en el detalle del alumno
- [x] 6.2 Ejecutar `npx ng test` (frontend) y confirmar que toda la suite pasa, y ejecutar la suite de tests de backend existente para confirmar que los ajustes del grupo 1 no rompen nada ya cubierto

## Workflow follow-up

- Abrir una rama `change/frontend-tech-lead-alumnos` y un PR hacia `develop` cuando los grupos 1-6 esten completos y verificados.
- Archivar el change (sincronizando el delta de `block-assignment` en su spec existente) una vez el PR este aprobado.
