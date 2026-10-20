# Spec Delta

## ADDED Requirements

### Requirement: Reintento ante token caducado en el frontend
El frontend SHALL reintentar una unica vez, con un token renovado, cualquier peticion a la API que el backend rechace con 401 por token invalido o caducado. Si la renovacion de sesion tambien falla, SHALL cerrar la sesion local y redirigir a login, propagando ademas el 401 original.

#### Scenario: El backend rechaza el token pero la renovacion de sesion funciona
- **WHEN** una peticion a la API responde 401 y la renovacion de sesion contra Supabase Auth obtiene un token nuevo
- **THEN** el frontend repite la misma peticion con el token nuevo y la operacion continua sin que el usuario vea el error

#### Scenario: La renovacion de sesion tambien falla
- **WHEN** una peticion a la API responde 401 y la renovacion de sesion no devuelve una sesion valida
- **THEN** el frontend cierra la sesion local, redirige a la pantalla de login y propaga el 401 original
