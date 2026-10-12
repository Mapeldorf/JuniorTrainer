# Spec Delta

## Purpose

Define como un alumno consulta sus propias asignaciones y el detalle de cada una (los ejercicios de su copia y si ya tiene respuesta), como base para poder responderlos.

## ADDED Requirements

### Requirement: Listar las propias asignaciones
El sistema SHALL permitir a un alumno listar unicamente sus propias asignaciones (bloque, fecha de asignacion), sin incluir asignaciones de otros alumnos.

#### Scenario: Un alumno lista sus asignaciones
- **WHEN** un alumno autenticado consulta su lista de asignaciones
- **THEN** recibe solo las asignaciones cuyo `student_id` es el suyo

#### Scenario: Un alumno sin asignaciones todavia
- **WHEN** un alumno autenticado sin ninguna asignacion consulta su lista de asignaciones
- **THEN** recibe una lista vacia

### Requirement: Ver el detalle de una asignacion propia
El sistema SHALL permitir a un alumno consultar el detalle de una asignacion suya (los ejercicios de su copia, en orden, y si cada uno ya tiene una respuesta registrada), y SHALL rechazar la consulta si la asignacion no es suya.

#### Scenario: Un alumno ve el detalle de su propia asignacion
- **WHEN** un alumno autenticado consulta el detalle de una asignacion suya
- **THEN** recibe los ejercicios de su copia en orden, cada uno indicando si ya tiene una respuesta registrada

#### Scenario: Un alumno intenta ver el detalle de la asignacion de otro
- **WHEN** un alumno autenticado intenta consultar el detalle de una asignacion que pertenece a otro alumno
- **THEN** la peticion se rechaza y no se devuelve ningun dato
