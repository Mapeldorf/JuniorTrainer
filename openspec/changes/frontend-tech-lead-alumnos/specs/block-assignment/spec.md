# Spec Delta

## ADDED Requirements

### Requirement: Consultar las asignaciones de un alumno a traves de sus bloques
El sistema SHALL permitir a un tech lead consultar, para un alumno dado, todas sus asignaciones; cada una SHALL incluir el nombre del bloque del que proviene y, para cada ejercicio de su copia, su tipo y enunciado, si tiene o no una respuesta registrada, y si la tiene, el texto de la respuesta, el verdict y la justificacion de su evaluacion; y SHALL rechazar la consulta si la hace un alumno.

#### Scenario: Ver las asignaciones de un alumno con varios bloques
- **WHEN** un tech lead consulta las asignaciones de un alumno que tiene varios bloques asignados
- **THEN** devuelve una entrada por asignacion, cada una con el nombre de su bloque y, para cada ejercicio de su copia, su tipo, su enunciado, y si tiene o no respuesta

#### Scenario: Un alumno sin asignaciones todavia
- **WHEN** un tech lead consulta las asignaciones de un alumno que no tiene ningun bloque asignado
- **THEN** recibe una lista vacia

#### Scenario: Una asignacion con respuestas evaluadas
- **WHEN** alguna de las asignaciones del alumno consultado ya tiene respuestas evaluadas para alguno de los ejercicios de su copia
- **THEN** esa asignacion muestra, para esos ejercicios, el texto de la respuesta, el verdict y la justificacion obtenidos en su evaluacion

#### Scenario: Un alumno no puede consultar las asignaciones de otro alumno por esta via
- **WHEN** un usuario con `role = student` intenta consultar las asignaciones de un alumno por este endpoint
- **THEN** la peticion responde 403 y no devuelve ningun dato
