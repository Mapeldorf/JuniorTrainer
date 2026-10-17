from fastapi import APIRouter, Depends

from app.deps import require_tech_lead
from app.schemas.profile import Profile
from app.schemas.technology import Technology
from app.supabase_client import get_admin_client

router = APIRouter(tags=["technologies"])


@router.get("/technologies")
async def list_technologies(
    _profile: Profile = Depends(require_tech_lead),
) -> list[Technology]:
    """Lista el catálogo canónico de tecnologías (change `catalogo-tecnologias`,
    capacidad technology-catalog: "Consulta del catálogo por el tech lead").
    Solo lectura; el tech lead lo usa para poblar el selector determinista del
    formulario de generación. Ordenado por nombre para una presentación estable."""
    result = (
        get_admin_client()
        .table("technology")
        .select("id, name")
        .order("name")
        .execute()
    )
    return [Technology(**row) for row in (result.data or [])]