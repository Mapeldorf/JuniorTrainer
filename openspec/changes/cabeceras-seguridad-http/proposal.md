# Proposal

## Why

El backend (FastAPI, `backend/app`) no añade ninguna cabecera de seguridad HTTP a sus respuestas hoy. Son protecciones baratas y estandar en cualquier backend en produccion (mitigan MIME-sniffing, clickjacking, fuga de referrer, y refuerzan el uso de HTTPS una vez desplegado detras de TLS), y actualmente faltan por completo.

## What Changes

- Añadir un middleware que incluya en toda respuesta HTTP:
  - `X-Content-Type-Options: nosniff` -- evita que el navegador reinterprete el `Content-Type` declarado (p. ej. tratar un JSON como HTML ejecutable).
  - `X-Frame-Options: DENY` -- evita que cualquier respuesta se embeba en un `<iframe>` (clickjacking).
  - `Referrer-Policy: strict-origin-when-cross-origin` -- evita filtrar la URL completa (que puede incluir datos sensibles en query strings) al navegar a un origen externo.
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains` -- indica a los navegadores que usen siempre HTTPS con este origen una vez se acceda por HTTPS (inocuo sobre HTTP plano en desarrollo local; solo tiene efecto cuando el navegador ya establecio la conexion por HTTPS).
- No se añade `Content-Security-Policy`: el backend es una API JSON pura (`proposal.md` de las propuestas anteriores confirma que todas las respuestas de negocio son JSON); el unico contenido HTML que sirve FastAPI por defecto es la documentacion interactiva (`/docs`, `/redoc`), que carga JS/CSS desde un CDN externo y se romperia con una CSP estricta sin una lista de origenes permitidos dedicada. Se documenta como decision en design.md, no como tarea de esta propuesta.

## Capabilities

### New Capabilities
- `api-security-headers`: cabeceras de seguridad HTTP presentes en toda respuesta del backend.

### Modified Capabilities
(ninguna: no cambia el comportamiento funcional de ningun endpoint, solo añade cabeceras a la respuesta)

## Impact

- Nuevo middleware en `backend/app` (p. ej. `app/security_headers.py`) registrado en `backend/app/main.py` junto a los middlewares ya existentes (limite de tamaño de body, CORS, rate limiting).
- Sin nueva dependencia: cabeceras añadidas directamente sobre la respuesta ASGI, sin libreria externa.
- Sin cambios en routers, schemas, ni en el contrato de ningun endpoint.
