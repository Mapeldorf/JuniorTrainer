from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.body_size_limit import BodySizeLimitMiddleware
from app.config import get_settings
from app.rate_limit import limiter
from app.routers import assignments, blocks, exercises, generations, health, technologies, users
from app.security_headers import SecurityHeadersMiddleware

settings = get_settings()

app = FastAPI(title="JuniorTrainer API")

# Limite de tamaño de body (propuesta limite-tamano-body).
app.add_middleware(BodySizeLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (propuesta rate-limiting-backend): limite por defecto a
# nivel de app en app/rate_limit.py, mas limites especificos decorados en
# los endpoints sensibles. El handler devuelve un cuerpo generico: no hay
# que exponer la configuracion del limite superado.
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Cabeceras de seguridad HTTP (propuesta cabeceras-seguridad-http): en
# Starlette, `add_middleware` inserta cada middleware al PRINCIPIO de la
# lista interna, asi que el ultimo en añadirse termina siendo el mas
# exterior de la cadena (lo contrario de lo que podria parecer a simple
# vista). Tiene que ser el ultimo `add_middleware` de todos para envolver
# tambien las respuestas de error que generan los middlewares de arriba
# (413 del limite de body, 429 del rate limiting), que de otro modo
# saldrian sin estas cabeceras.
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(RateLimitExceeded)
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # SlowAPIMiddleware solo soporta handlers sincronos (ver
    # slowapi.middleware.sync_check_limits): uno async cae de vuelta al
    # handler por defecto, que expone la configuracion del limite superado.
    return JSONResponse(
        status_code=429,
        content={"detail": "Demasiadas peticiones, intentalo mas tarde"},
    )

app.include_router(health.router)
app.include_router(users.router)
app.include_router(generations.router)
app.include_router(technologies.router)
app.include_router(exercises.router)
app.include_router(blocks.router)
app.include_router(assignments.router)
