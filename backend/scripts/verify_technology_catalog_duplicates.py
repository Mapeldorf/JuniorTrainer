"""Verificacion manual (sin servidor HTTP) de `POST /technologies` para el
change `validador-duplicados-tecnologias`: un rechazo del validador por
duplicado semantico (`duplicate_technologies` no vacio) devuelve 409, no el
422 generico que sigue aplicando a una entrada que simplemente no es una
tecnologia de programacion.

Llama directamente a `technologies.create_technology` (sin levantar un
servidor HTTP) con `send_a2a_task` sustituido por una respuesta simulada del
validador -- mismo patron que `verify_ejercicios_tech_lead.py`. No necesita
el agente validador arrancado; necesita el proyecto Supabase real del .env
de la raiz (para la comprobacion de duplicado exacto y el alta misma).

Uso (desde backend/, con el venv del backend activo):
    python -m scripts.verify_technology_catalog_duplicates
"""

import asyncio
import uuid

from fastapi import HTTPException

import app.routers.technologies as technologies
from app.schemas.profile import Profile
from app.schemas.technology import NewTechnologyRequest
from app.supabase_client import get_admin_client

TAG = f"verify-dup-{uuid.uuid4().hex[:8]}"


async def _fake_validator_semantic_duplicate(*_args, **_kwargs) -> dict:
    return {
        "valid": False,
        "reason": f"ya existe en el catalogo como 'TypeScript ({TAG})'",
        "invalid_technologies": [],
        "duplicate_technologies": [
            {"input": f"TS ({TAG})", "matches": f"TypeScript ({TAG})"}
        ],
    }


async def _fake_validator_not_a_technology(*_args, **_kwargs) -> dict:
    return {
        "valid": False,
        "reason": "no es una tecnologia de programacion",
        "invalid_technologies": [f"no-tech ({TAG})"],
        "duplicate_technologies": [],
    }


async def main() -> None:
    admin = get_admin_client()

    tech_lead_rows = (
        admin.table("profile").select("id, email, name").eq("role", "tech_lead").limit(1).execute().data
    )
    if not tech_lead_rows:
        raise SystemExit(
            "no hay ningun profile con role='tech_lead' todavia -- "
            "crea uno con `python -m scripts.seed_tech_lead` primero"
        )
    tech_lead_row = tech_lead_rows[0]
    tech_lead = Profile(
        id=tech_lead_row["id"],
        email=tech_lead_row["email"],
        name=tech_lead_row["name"],
        role="tech_lead",
    )

    original_send_a2a_task = technologies.send_a2a_task

    try:
        # --- Rechazo por duplicado semantico: 409, no 422 ---
        technologies.send_a2a_task = _fake_validator_semantic_duplicate
        try:
            await technologies.create_technology(
                NewTechnologyRequest(name=f"TS ({TAG})"), _profile=tech_lead
            )
        except HTTPException as exc:
            assert exc.status_code == 409, (
                f"un duplicado semantico deberia devolver 409, no {exc.status_code}"
            )
        else:
            raise AssertionError("el alta deberia haberse rechazado")
        print("OK: duplicado semantico (duplicate_technologies no vacio) -> 409")

        # --- Rechazo por no ser una tecnologia: sigue siendo 422 ---
        technologies.send_a2a_task = _fake_validator_not_a_technology
        try:
            await technologies.create_technology(
                NewTechnologyRequest(name=f"no-tech ({TAG})"), _profile=tech_lead
            )
        except HTTPException as exc:
            assert exc.status_code == 422, (
                f"una entrada invalida deberia seguir devolviendo 422, no {exc.status_code}"
            )
        else:
            raise AssertionError("el alta deberia haberse rechazado")
        print("OK: entrada invalida (sin duplicate_technologies) -> sigue siendo 422")
    finally:
        technologies.send_a2a_task = original_send_a2a_task
        # Ninguno de los dos casos llega a insertar fila (ambos se rechazan
        # antes del insert), asi que no hace falta limpieza en la tabla
        # technology -- se deja constancia por si un futuro cambio en el
        # endpoint lo hiciera inseguro por omision.


if __name__ == "__main__":
    asyncio.run(main())
