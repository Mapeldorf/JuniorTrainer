# Spec Delta

## MODIFIED Requirements

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
