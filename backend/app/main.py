from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, users

settings = get_settings()

app = FastAPI(title="JuniorTrainer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router)

# El resto de /users (listar alumnos, ver sus asignaciones) y los routers de
# generaciones, bloques, asignaciones y respuestas (seccion 9 de la
# especificacion) llegan en los pasos 2 y 3 del plan de trabajo, junto con los
# agentes que los alimentan.
