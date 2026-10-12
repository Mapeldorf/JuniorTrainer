# student-assignments Specification

## Purpose

Define como un alumno consulta sus propias asignaciones y el detalle de cada una (los ejercicios de su copia y si ya tiene respuesta), como base para poder responderlos.

## Requirements

### Requirement: Listar las propias asignaciones
El sistema SHALL permitir a un alumno listar unicamente sus propias asignaciones (bloque, fecha de asignacion, y cuantos de sus ejercicios tienen ya respuesta sobre el total), sin incluir asignaciones de otros alumnos.

#### Scenario: Un alumno lista sus asignaciones
- **WHEN** un alumno autenticado consulta su lista de asignaciones
- **THEN** recibe solo las asignaciones cuyo `student_id` es el suyo, cada una con el numero de ejercicios respondidos y el total de su copia

#### Scenario: Un alumno sin asignaciones todavia
- **WHEN** un alumno autenticado sin ninguna asignacion consulta su lista de asignaciones
- **THEN** recibe una lista vacia

#### Scenario: Progreso de una asignacion sin respuestas todavia
- **WHEN** una asignacion de la lista no tiene ninguna respuesta registrada
- **THEN** su numero de ejercicios respondidos es cero

#### Scenario: Progreso de una asignacion completada
- **WHEN** todos los ejercicios de la copia de una asignacion ya tienen respuesta
- **THEN** su numero de ejercicios respondidos coincide con el total

### Requirement: Ver el detalle de una asignacion propia
El sistema SHALL permitir a un alumno consultar el detalle de una asignacion suya: los ejercicios de su copia en el orden del bloque, hasta el primero sin responder inclusive, cada uno con su respuesta, verdict y justificacion si ya la tiene; y SHALL rechazar la consulta si la asignacion no es suya.

#### Scenario: Un alumno ve el detalle de su propia asignacion
- **WHEN** un alumno autenticado consulta el detalle de una asignacion suya que tiene ejercicios aun sin responder
- **THEN** recibe los ejercicios de su copia en orden hasta el primero sin responder inclusive, y no recibe ningun ejercicio posterior a ese

#### Scenario: Un ejercicio ya respondido incluye su valoracion
- **WHEN** el detalle consultado incluye un ejercicio con una respuesta ya registrada
- **THEN** ese ejercicio incluye el texto de la respuesta del alumno, el verdict y la justificacion

#### Scenario: Un alumno ve el detalle de una asignacion completada
- **WHEN** todos los ejercicios de la copia de una asignacion ya tienen respuesta registrada
- **THEN** recibe todos los ejercicios de la copia, cada uno con su respuesta, verdict y justificacion

#### Scenario: Un alumno intenta ver el detalle de la asignacion de otro
- **WHEN** un alumno autenticado intenta consultar el detalle de una asignacion que pertenece a otro alumno
- **THEN** la peticion se rechaza y no se devuelve ningun dato
