# Spec Delta

## ADDED Requirements

### Requirement: Listar alumnos
El sistema SHALL permitir a un tech lead listar los alumnos existentes (identificador, nombre y email), y SHALL rechazar esta consulta si la hace un alumno.

#### Scenario: Tech lead lista los alumnos
- **WHEN** un tech lead autenticado llama a `GET /users`
- **THEN** recibe la lista de todos los alumnos existentes con su identificador, nombre y email

#### Scenario: Un alumno no puede listar alumnos
- **WHEN** un usuario autenticado con `role = student` llama a `GET /users`
- **THEN** la peticion responde 403 y no devuelve ningun dato
