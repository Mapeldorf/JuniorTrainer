from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import blocks, exercises, generations, health, users

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
app.include_router(generations.router)
app.include_router(exercises.router)
app.include_router(blocks.router)

# El resto de /users (listar alumnos) y los endpoints de respuesta del
# alumno + agentes evaluador/revisor (seccion 9 de la especificacion)
# llegan en el change siguiente, "valoracion-respuestas".
