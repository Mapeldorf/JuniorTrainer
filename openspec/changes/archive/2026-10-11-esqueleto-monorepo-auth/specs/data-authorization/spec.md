# Spec Delta

## Purpose

Define, a nivel de base de datos, que puede leer o escribir cada rol (tech lead o alumno) y que filas se vuelven inmutables una vez guardadas, asignadas o respondidas, con independencia de la capa de API que las llame.

## ADDED Requirements

### Requirement: Alcance de lectura por rol
El sistema SHALL restringir, mediante Row Level Security, que un alumno solo vea su propio `profile`, las generaciones/bloques/ejercicios que el tech lead gestiona SHALL permanecer invisibles para los alumnos salvo a traves de su propia copia de asignacion.

#### Scenario: Un alumno lee ejercicios fuera de su asignacion
- **WHEN** un usuario con `role = student` consulta la tabla `exercise` por un ejercicio que no forma parte de ninguna de sus asignaciones
- **THEN** la consulta no devuelve esa fila

#### Scenario: Un alumno lee la asignacion de otro alumno
- **WHEN** un usuario con `role = student` consulta `assignment` o `assignment_exercise` de un `student_id` que no es el suyo
- **THEN** la consulta no devuelve esas filas

#### Scenario: El tech lead lee cualquier perfil
- **WHEN** un usuario con `role = tech_lead` consulta la tabla `profile`
- **THEN** la consulta devuelve todos los perfiles, no solo el suyo

### Requirement: Un ejercicio guardado es inmutable
Una vez que un `exercise` tiene `saved = true`, el sistema SHALL impedir cambios a su enunciado, codigo, tipo, generacion de origen o respuesta esperada; `deleted_at` SHALL seguir siendo modificable para poder eliminarlo de la aplicacion.

#### Scenario: Intentar editar el enunciado de un ejercicio guardado
- **WHEN** se intenta actualizar `statement` de un `exercise` cuyo `saved` ya es `true`
- **THEN** la base de datos rechaza la operacion

#### Scenario: Eliminar un ejercicio guardado
- **WHEN** se actualiza solo `deleted_at` de un `exercise` cuyo `saved` ya es `true`
- **THEN** la base de datos acepta la operacion

### Requirement: Solo ejercicios guardados entran en un bloque
El sistema SHALL impedir que un ejercicio sin `saved = true`, o ya eliminado, se añada a `block_exercise`.

#### Scenario: Añadir a un bloque un ejercicio no guardado
- **WHEN** se intenta insertar en `block_exercise` un `exercise_id` cuyo `saved` es `false`
- **THEN** la base de datos rechaza la operacion

#### Scenario: Añadir a un bloque un ejercicio eliminado
- **WHEN** se intenta insertar en `block_exercise` un `exercise_id` cuyo `deleted_at` no es nulo
- **THEN** la base de datos rechaza la operacion

### Requirement: La copia de una asignacion es inmutable
Una vez creada una fila de `assignment_exercise` (la copia de `block_exercise` al asignar), el sistema SHALL impedir cualquier modificacion posterior, aunque el bloque de origen cambie despues.

#### Scenario: Editar una fila de assignment_exercise ya creada
- **WHEN** se intenta hacer `UPDATE` sobre una fila existente de `assignment_exercise`
- **THEN** la base de datos rechaza la operacion

### Requirement: Una respuesta no se modifica
El sistema SHALL impedir cualquier modificacion de una fila de `answer` despues de haberse creado, y SHALL exigir que cada respuesta corresponda a un ejercicio presente en la copia de esa misma asignacion.

#### Scenario: Editar una respuesta ya dada
- **WHEN** se intenta hacer `UPDATE` sobre una fila existente de `answer`
- **THEN** la base de datos rechaza la operacion

#### Scenario: Responder a un ejercicio fuera de la copia de la asignacion
- **WHEN** se intenta insertar en `answer` una pareja `(assignment_id, exercise_id)` que no existe en `assignment_exercise`
- **THEN** la base de datos rechaza la operacion por la clave foranea compuesta
