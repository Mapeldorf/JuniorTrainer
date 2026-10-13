# Tasks

## 1. Middleware de cabeceras

- [x] 1.1 Crear `backend/app/security_headers.py` con un middleware ASGI puro que envuelva `send()`, intercepte el mensaje `http.response.start` y añada `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y `Strict-Transport-Security` solo si no estan ya presentes. Verificar que el modulo importa sin errores (`python -c "import app.security_headers"`).

## 2. Integracion en la app

- [x] 2.1 Registrar el middleware en `backend/app/main.py` como el ultimo añadido (el mas exterior de la cadena), y verificar que el import check del CI (`python -c "from app.main import app"`) sigue pasando. Nota de implementacion: `add_middleware` inserta al principio de la lista interna de Starlette, asi que el ultimo en añadirse es el mas exterior (lo contrario de lo que parece a simple vista) -- se detecto en la verificacion manual (tarea 3.2) que con el orden inicial el `429` no llevaba las cabeceras, y se corrigio moviendo `SecurityHeadersMiddleware` al final de los `add_middleware`.

## 3. Verificacion manual

- [x] 3.1 Levantar el backend localmente (`uvicorn app.main:app`) y verificar con `curl -i` que `GET /health` (respuesta de exito) incluye las cuatro cabeceras con los valores esperados.
- [x] 3.2 Verificar con `curl -i` que una respuesta de error generada por un middleware existente (p. ej. `429` del rate limiting, forzando una rafaga de peticiones, o `413` del limite de body con un `Content-Length` grande) tambien incluye las cuatro cabeceras. Se detecto que con el orden inicial de `add_middleware` el `429` salia sin cabeceras (`SecurityHeadersMiddleware` quedaba mas interior que `SlowAPIMiddleware`); corregido el orden en `main.py`, verificado que `429` y `413` ya incluyen las cuatro cabeceras.
- [x] 3.3 Verificar con `curl -i` que una respuesta `401`/`404` generada por un router normal (p. ej. `GET /users` sin token) tambien incluye las cuatro cabeceras. Verificado: `401 {"detail":"Falta el token de autenticacion"}` incluye las cuatro cabeceras.
