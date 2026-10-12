# Spec Delta

## MODIFIED Requirements

### Requirement: Consultar el progreso de un bloque asignado
El sistema SHALL permitir a un tech lead consultar, para cada alumno asignado a un bloque, si tiene o no una respuesta registrada por cada ejercicio de su copia, y el verdict de cada ejercicio ya respondido.

#### Scenario: Ver el progreso de un bloque con varios alumnos
- **WHEN** un tech lead consulta el progreso de un bloque con varios alumnos asignados
- **THEN** devuelve, por alumno, que ejercicios de su copia tienen respuesta y cuales no, y el verdict de los que ya tienen respuesta

#### Scenario: Progreso de un alumno sin respuestas todavia
- **WHEN** un alumno asignado todavia no ha respondido a ningun ejercicio de su copia
- **THEN** su progreso muestra todos los ejercicios de la copia sin respuesta y sin verdict

#### Scenario: Progreso de un alumno con respuestas evaluadas
- **WHEN** un alumno asignado ya tiene respuestas evaluadas para alguno de los ejercicios de su copia
- **THEN** su progreso muestra, para esos ejercicios, el verdict obtenido en su evaluacion
