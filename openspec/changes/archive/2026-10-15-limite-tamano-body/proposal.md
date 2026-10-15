# Proposal

## Why

El backend (FastAPI, `backend/app`) no limita el tamaño del body de ninguna peticion HTTP. Cualquier `POST`/`PATCH` (incluidos los ya protegidos por autenticacion y por el rate limiting de la propuesta `rate-limiting-backend`, ya implementada) acepta payloads de cualquier tamaño: un cliente puede enviar varios megabytes u mas en un solo request, obligando al proceso a leerlos y a Pydantic a intentar parsearlos, con coste de memoria y CPU. Es un vector de denegacion de servicio trivial que no requiere ni siquiera superar el rate limit (basta una peticion grande).

## What Changes

- Añadir un middleware ASGI al backend que rechace con `413 Content Too Large` cualquier peticion cuyo body supere un limite fijo (tamaño de partida: 1 MiB, generoso para los payloads reales del dominio -- invitar alumnos, enunciados/codigo de ejercicios, respuestas de alumnos -- que son texto corto).
- El rechazo ocurre antes de que FastAPI/Pydantic procesen el payload completo:
  - Si la peticion trae `Content-Length` y supera el limite, se rechaza inmediatamente sin leer el body.
  - Si no trae `Content-Length` (cuerpo chunked) o miente sobre su tamaño, el middleware cuenta los bytes reales recibidos y corta en cuanto se supera el limite, sin esperar a que el cliente termine de enviar un body arbitrariamente grande.
- El cuerpo de la respuesta `413` es generico (no expone el limite exacto ni configuracion interna), consistente con la propuesta `api-error-handling` ya implementada.

## Capabilities

### New Capabilities
- `api-body-size-limit`: limite de tamaño maximo del body de las peticiones HTTP al backend, aplicado de forma transversal a todos los endpoints.

### Modified Capabilities
(ninguna: no cambia el comportamiento funcional de ningun endpoint para peticiones dentro del limite, solo rechaza las que lo superan)

## Impact

- Nuevo middleware ASGI en `backend/app` (modulo nuevo, p. ej. `app/body_size_limit.py`) registrado en `backend/app/main.py` junto al resto de middlewares (CORS, rate limiting).
- Sin cambios en los routers ni en los schemas Pydantic existentes.
- Sin nueva dependencia: se implementa con ASGI puro (`Scope`/`Receive`/`Send` de Starlette), ya disponible via `fastapi`/`starlette`.
