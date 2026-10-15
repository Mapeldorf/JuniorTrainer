# api-rate-limiting Specification

## Purpose
Limita la frecuencia de peticiones que un mismo usuario autenticado puede hacer al backend, para mitigar fuerza bruta y abuso de endpoints costosos.

## Requirements

### Requirement: Limite por defecto en endpoints autenticados
El sistema SHALL aplicar un limite de frecuencia por defecto a todas las peticiones a endpoints que requieran autenticacion, identificando al llamante por el `id` del perfil resuelto del token.

#### Scenario: Peticiones dentro del limite
- **WHEN** un usuario autenticado hace peticiones a un ritmo por debajo del limite por defecto
- **THEN** todas las peticiones se procesan con normalidad

#### Scenario: Peticiones por encima del limite por defecto
- **WHEN** un usuario autenticado supera el limite por defecto de peticiones en la ventana configurada
- **THEN** el sistema responde con `429 Too Many Requests` a las peticiones adicionales, con un mensaje generico sin detalles internos

### Requirement: Limite estricto en alta de alumnos
El sistema SHALL aplicar un limite de frecuencia mas estricto que el limite por defecto al endpoint de alta/invitacion de alumnos (`POST /users`), por tech lead autenticado.

#### Scenario: Invitaciones repetidas superan el limite
- **WHEN** un tech lead autenticado invoca `POST /users` mas veces de las permitidas por el limite estricto dentro de la ventana configurada
- **THEN** las invitaciones adicionales se rechazan con `429 Too Many Requests` y no se llega a invocar la Admin API de Supabase

### Requirement: Limite estricto en inicio de generaciones
El sistema SHALL aplicar un limite de frecuencia mas estricto que el limite por defecto a los endpoints que inician una generacion contra los agentes, por usuario autenticado.

#### Scenario: Inicios de generacion repetidos superan el limite
- **WHEN** un usuario autenticado inicia generaciones mas veces de las permitidas por el limite estricto dentro de la ventana configurada
- **THEN** las peticiones adicionales se rechazan con `429 Too Many Requests` y no se llega a invocar a los agentes de generacion

### Requirement: Respuesta sin detalles internos al superar el limite
El sistema SHALL devolver, cuando se supera cualquier limite de frecuencia, una respuesta `429` con un cuerpo que no exponga configuracion interna (claves de limite, almacenamiento usado, etc.), mas alla de informar que se ha superado el limite.

#### Scenario: Cuerpo de la respuesta 429
- **WHEN** cualquier limite de frecuencia se supera
- **THEN** el cuerpo de la respuesta indica unicamente que se ha superado el limite de peticiones, sin datos de implementacion
