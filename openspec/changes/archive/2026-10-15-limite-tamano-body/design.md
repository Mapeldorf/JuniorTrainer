# Design

## Context

El backend es FastAPI sobre Starlette/uvicorn (`backend/app/main.py`), que ya registra `CORSMiddleware` y `SlowAPIMiddleware` (propuesta `rate-limiting-backend`, implementada). Ninguno de los dos limita el tamaño del body: Starlette no impone un limite por defecto, y FastAPI/Pydantic leen el body completo en memoria antes de validar. Los payloads legitimos del dominio son texto corto (invitar alumno, enunciado/codigo de un ejercicio, respuesta de un alumno); no hay ningun caso de uso que suba ficheros o payloads grandes. Ver `proposal.md` para el motivo.

## Goals / Non-Goals

**Goals:**
- Que ninguna peticion con un body mayor que el limite configurado llegue a ejecutar el endpoint ni el parseo de Pydantic.
- Que el limite se aplique de forma transversal (un unico middleware), sin tener que anotar cada endpoint.
- Que un cliente no pueda saltarse el limite omitiendo o mintiendo en `Content-Length`.

**Non-Goals:**
- No se distingue limite por endpoint: un unico limite global es suficiente porque todos los payloads legitimos son pequeños (ver Context). Si en el futuro se añade subida de ficheros, ese endpoint necesitaria su propio limite mayor, fuera de alcance aqui.
- No se usa un proxy/gateway externo (nginx, Cloudflare) para este limite: la infraestructura actual (`docker-compose.yml`) no tiene un proxy delante del backend; el limite vive en la aplicacion.
- No se streamea el body a disco ni se procesan subidas multipart grandes: simplemente se corta la conexion si se supera el limite.

## Decisions

- **Middleware ASGI puro, no `BaseHTTPMiddleware`.** `BaseHTTPMiddleware` (la que ya usa `SlowAPIMiddleware`) bufferea el body para poder leerlo dos veces, lo que anula el propio objetivo de cortar antes de leer todo el body. Un middleware ASGI puro que envuelve `receive()` puede contar bytes y cortar en cuanto se supera el limite, sin leer de mas. Alternativa descartada: `BaseHTTPMiddleware` con `request.stream()` -- mas simple de escribir pero bufferea igualmente por como Starlette reconstruye el stream para los middlewares de ese tipo.
- **Limite por `Content-Length` primero, conteo real como respaldo.** Si el header esta presente y ya supera el limite, se rechaza sin leer ningun byte del body (barato). Si no esta presente, es menor que el real, o el cliente envia mas de lo declarado, el middleware cuenta los bytes de cada mensaje `http.request` recibido via `receive()` y corta en cuanto el acumulado supera el limite, devolviendo `413` y dejando de invocar `receive()`/la app. Cubre el caso de un cliente malicioso que omite o falsea `Content-Length`.
- **Limite inicial: 1 MiB.** Generoso para cualquier payload legitimo actual (varios ordenes de magnitud por encima de un enunciado o respuesta de texto), documentado como constante en el propio middleware para poder ajustarlo sin cambiar la spec.
- **Respuesta 413 generica.** Mismo patron que la propuesta `api-error-handling`: el cuerpo no incluye el limite configurado ni detalles de implementacion.

## Risks / Trade-offs

- [Un middleware ASGI puro es mas dificil de leer/mantener que uno basado en `BaseHTTPMiddleware`] -> Mitigacion: el middleware es pequeño y autocontenido (un solo fichero, una sola responsabilidad), con comentarios explicando por que no se usa `BaseHTTPMiddleware`.
- [Un limite global de 1 MiB podria quedarse corto si en el futuro se añaden adjuntos o subida de ficheros] -> Mitigacion: es una constante de configuracion, revisable sin cambiar el contrato de la API; si se añade subida de ficheros, esa propuesta decidiria un limite especifico para ese endpoint.
- [Cortar la conexion a mitad de un body chunked podria dejar la conexion en un estado inconsistente para algunos clientes] -> Mitigacion: se responde `413` y se cierra la respuesta de forma ordenada (enviar la respuesta ASGI completa), comportamiento estandar para este tipo de proteccion y equivalente a lo que hacen proxies como nginx con `client_max_body_size`.
