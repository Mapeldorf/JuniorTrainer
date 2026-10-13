from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.rate_limit import limiter
from app.routers import assignments, blocks, exercises, generations, health, users

settings = get_settings()

app = FastAPI(title="JuniorTrainer API")

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
app.include_router(exercises.router)
app.include_router(blocks.router)
app.include_router(assignments.router)
