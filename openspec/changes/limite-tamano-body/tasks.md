# Tasks

## 1. Middleware de limite de tamaño

- [x] 1.1 Crear `backend/app/body_size_limit.py` con un middleware ASGI puro (`scope`/`receive`/`send`) que: (a) si `Content-Length` supera el limite, responda `413` sin invocar `receive()`; (b) si no, cuente los bytes reales de cada mensaje `http.request` y corte con `413` en cuanto se supere el limite. Verificar que el modulo importa sin errores (`python -c "import app.body_size_limit"`). Nota de implementacion: la señal interna de corte (`_BodyTooLarge`) hereda de `BaseException`, no de `Exception` -- FastAPI envuelve el parseo del body en un `except Exception` generico (`routing.py`) que, si heredara de `Exception`, la convertiria en un `400 "There was an error parsing the body"` antes de llegar a este middleware (comprobado en la verificacion manual de la tarea 3.3).
- [x] 1.2 Documentar la constante del limite (1 MiB) en el propio modulo, y el cuerpo generico de la respuesta `413` (sin exponer el valor del limite).

## 2. Integracion en la app

- [x] 2.1 Registrar el middleware en `backend/app/main.py` (antes del resto, para cortar lo antes posible en la cadena ASGI), y verificar que el import check del CI (`python -c "from app.main import app"`) sigue pasando.

## 3. Verificacion manual

- [x] 3.1 Levantar el backend localmente (`uvicorn app.main:app`) y verificar con curl/httpie que una peticion normal (p. ej. `GET /health`, o un POST pequeño) sigue respondiendo igual que antes del cambio. Verificado: `GET /health` sigue devolviendo `200`.
- [x] 3.2 Verificar con curl que un POST con `Content-Length` declarado por encima del limite (p. ej. `curl -H "Content-Length: 5000000" ...` o un body real generado con `head -c` de /dev/urandom) recibe `413` con el cuerpo generico, sin que el endpoint llegue a ejecutarse. Verificado: `413 {"detail":"El cuerpo de la peticion es demasiado grande"}`, rechazado sin leer el body.
- [x] 3.3 Verificar con curl (`-H "Transfer-Encoding: chunked"` o equivalente) que un body enviado sin `Content-Length` fiable y por encima del limite tambien corta con `413`, no solo el caso con `Content-Length` explicito. Verificado con un body chunked de ~2 MB: primero se detecto el bug descrito en la tarea 1.1 (devolvia `400` en vez de `413`), corregido cambiando `_BodyTooLarge` a `BaseException`; tras el fix, `413 {"detail":"El cuerpo de la peticion es demasiado grande"}` y el servidor sigue sano despues del corte (`GET /health` vuelve a responder `200`).
