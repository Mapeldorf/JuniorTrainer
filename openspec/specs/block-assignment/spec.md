# block-assignment Specification

## Purpose

Define como se asigna un bloque de ejercicios a uno o varios alumnos con una copia propia e inmutable, y como se consulta su progreso de respuesta.

## Requirements

### Requirement: Asignar un bloque crea una copia inmutable de sus ejercicios
El sistema SHALL permitir a un tech lead asignar un bloque, activo y no eliminado, a uno o varios alumnos; cada asignacion SHALL copiar en ese momento los ejercicios del bloque, y esa copia SHALL dejar de verse afectada por cualquier cambio posterior al bloque, a sus ejercicios, o a su borrado logico.

#### Scenario: Asignar un bloque a varios alumnos
- **WHEN** un tech lead asigna un bloque activo a una lista de alumnos
- **THEN** se crea una asignacion por alumno, cada una con su propia copia de los ejercicios del bloque en ese momento

#### Scenario: Asignar el mismo bloque dos veces al mismo alumno
- **WHEN** se intenta asignar a un alumno un bloque que ya tiene asignado
- **THEN** la peticion se rechaza y no se crea una segunda asignacion

#### Scenario: Asignar un bloque eliminado
- **WHEN** se intenta asignar un bloque que esta en "Bloques eliminados"
- **THEN** la peticion se rechaza y no se crea ninguna asignacion

#### Scenario: Cambios posteriores no afectan a una copia ya creada
- **WHEN** despues de asignar un bloque se edita su nombre o su composicion, o se elimina alguno de sus ejercicios o el bloque mismo
- **THEN** las copias de ejercicios ya asignadas a los alumnos no cambian

### Requirement: Consultar el progreso de un bloque asignado
El sistema SHALL permitir a un tech lead consultar, para cada alumno asignado a un bloque, su identificador y su nombre, y para cada ejercicio de su copia su tipo y enunciado, si tiene o no una respuesta registrada, y si la tiene, el texto de la respuesta, el verdict y la justificacion de su evaluacion.

#### Scenario: Ver el progreso de un bloque con varios alumnos
- **WHEN** un tech lead consulta el progreso de un bloque con varios alumnos asignados
- **THEN** devuelve, por alumno, su nombre, y para cada ejercicio de su copia su tipo, su enunciado, y si tiene o no respuesta

#### Scenario: Progreso de un alumno sin respuestas todavia
- **WHEN** un alumno asignado todavia no ha respondido a ningun ejercicio de su copia
- **THEN** su progreso muestra todos los ejercicios de la copia sin respuesta, sin texto de respuesta, sin verdict y sin justificacion

#### Scenario: Progreso de un alumno con respuestas evaluadas
- **WHEN** un alumno asignado ya tiene respuestas evaluadas para alguno de los ejercicios de su copia
- **THEN** su progreso muestra, para esos ejercicios, el texto de la respuesta, el verdict y la justificacion obtenidos en su evaluacion
