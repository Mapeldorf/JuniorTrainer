# Proposal

## Why

El backend (FastAPI, `backend/app`) no tiene ningun limite de frecuencia de peticiones. Cualquiera con un token valido (o intentando conseguirlo) puede llamar en bucle a endpoints sensibles: `POST /users` (alta de alumnos via Supabase Admin API) y los endpoints de `generations.py` que disparan llamadas a los agentes de generacion, con coste real en tokens de LLM. Sin un limite basico, estos endpoints son vectores triviales de abuso y de denegacion de servicio.

## What Changes

- Añadir rate limiting a nivel de aplicacion en el backend FastAPI usando `slowapi` (basado en `limits`), con almacenamiento en memoria por proceso como backend por defecto (sin dependencia nueva de infraestructura).
- Aplicar un limite por defecto, mas permisivo, a todos los endpoints autenticados.
- Aplicar un limite mas estricto y especifico a:
  - `POST /users` (alta/invitacion de alumnos): limita fuerza bruta y spam de invitaciones.
  - Los endpoints de `generations.py` que inician una generacion contra los agentes: limita el coste de abuso (llamadas a LLM).
- Identificar al llamante por el `student_id`/`tech_lead` del token validado (no solo por IP), ya que todas las rutas afectadas ya exigen autenticacion.
- Devolver `429 Too Many Requests` con un mensaje generico cuando se supera el limite.

## Capabilities

### New Capabilities
- `api-rate-limiting`: limites de frecuencia de peticiones por usuario autenticado en los endpoints del backend, con limites especificos para altas de usuarios y generaciones.

### Modified Capabilities
(ninguna: no cambia el comportamiento funcional de `user-auth` ni `exercise-generation`, solo añade un limite transversal)

## Impact

- `backend/app/main.py`: registrar el `Limiter` y el exception handler de `RateLimitExceeded`.
- `backend/app/routers/users.py`: decorador de limite estricto en `invite_student`.
- `backend/app/routers/generations.py`: decorador de limite estricto en el/los endpoint(s) que inician generaciones.
- `backend/requirements.txt`: nueva dependencia `slowapi`.
- Sin cambios en esquema de base de datos ni en contratos de API existentes (los endpoints responden igual salvo cuando se supera el limite).
