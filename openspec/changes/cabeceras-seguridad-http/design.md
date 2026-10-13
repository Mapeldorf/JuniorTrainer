# Design

## Context

El backend ya registra tres middlewares propios (`BodySizeLimitMiddleware`, `CORSMiddleware`, `SlowAPIMiddleware`) en `backend/app/main.py`, ademas de `app.exception_handler(RateLimitExceeded)`. No hay proxy/gateway delante del backend en la infraestructura actual (`docker-compose.yml` publica el puerto 8000 directamente); cualquier terminacion TLS en produccion ocurriria fuera de este repo. FastAPI expone por defecto `/docs` y `/redoc` (Swagger UI / ReDoc), que son HTML y cargan JS/CSS desde un CDN externo. Ver `proposal.md` para el motivo y por que no se añade CSP.

## Goals / Non-Goals

**Goals:**
- Que las cuatro cabeceras listadas en la spec aparezcan en toda respuesta, incluidas las de error generadas por los middlewares existentes (rate limit 429, body size 413, excepciones no capturadas).
- Que añadir las cabeceras no requiera tocar cada router ni cada `HTTPException` existente.

**Non-Goals:**
- No se añade `Content-Security-Policy` (ver proposal.md - What Changes): romperia `/docs`/`/redoc` sin una lista de origenes permitidos dedicada, y el valor que aporta a una API JSON pura es bajo comparado con el riesgo de romper la documentacion interactiva. Si en el futuro se quiere networkear CSP, seria una propuesta aparte que decida explicitamente que hacer con `/docs`/`/redoc` (excluirlos, deshabilitarlos en produccion, o darles una CSP propia).
- No se decide aqui si `/docs`/`/redoc` deben deshabilitarse en produccion: es una decision de despliegue ortogonal a añadir cabeceras de seguridad, fuera de alcance.
- `Strict-Transport-Security` se envia siempre, independientemente de si la conexion actual es HTTP o HTTPS: los navegadores solo aplican la directiva cuando la respuesta llega por una conexion HTTPS ya establecida, asi que enviarla sobre HTTP plano (como en desarrollo local) es inocuo. No se intenta detectar el esquema de la peticion para condicionar el envio.

## Decisions

- **Middleware ASGI puro, igual que `BodySizeLimitMiddleware`.** Añadir cabeceras a toda respuesta (incluidas las que generan los middlewares existentes y los handlers de excepcion) es mas simple interceptando el mensaje `http.response.start` del lado de `send`, sin depender de que cada handler individual las añada. Alternativa descartada: usar `BaseHTTPMiddleware` (como `SlowAPIMiddleware`) -- funcionaria para el caso normal, pero ya hemos visto en la propuesta `limite-tamano-body` que `BaseHTTPMiddleware` interactua mal con excepciones que cruzan capas; un middleware ASGI puro que solo envuelve `send()` (no `receive()`) es ademas mas simple que el de esa propuesta, al no tener que lidiar con esa interaccion.
- **Añadido como ultimo paso de la cadena de middlewares (el que envuelve mas cerca de la respuesta final).** Para garantizar que las cabeceras se añaden a TODA respuesta, incluidas las generadas por middlewares internos de FastAPI/Starlette (`ServerErrorMiddleware`, `ExceptionMiddleware`) y por los otros middlewares de la app, este middleware debe ser el mas exterior de todos: se registra con `app.add_middleware(...)` en ultimo lugar (Starlette hace que el ultimo middleware añadido sea el mas exterior, ver `design.md` de `limite-tamano-body` para el razonamiento sobre el orden de `add_middleware`).
- **No sobreescribir una cabecera que un handler ya hubiera puesto.** Si en el futuro algun endpoint necesitara un valor distinto para alguna de estas cabeceras, el middleware solo añade la cabecera si no esta ya presente en la respuesta, evitando una duplicacion silenciosa.

## Risks / Trade-offs

- [Un middleware que envuelve `send()` para todas las respuestas añade una capa mas a la cadena ASGI, con un coste de rendimiento marginal] -> Mitigacion: la operacion es solo inspeccionar/añadir unas pocas cabeceras en un diccionario, coste despreciable frente al resto del request.
- [No añadir CSP deja sin cubrir un vector de XSS si en el futuro el backend empezara a servir HTML propio (no solo `/docs`/`/redoc`)] -> Mitigacion: hoy no sirve HTML de negocio; si eso cambiara, seria el momento de revisar esta decision con una CSP especifica para ese contenido nuevo.
