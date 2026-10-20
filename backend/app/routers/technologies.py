from fastapi import APIRouter, Depends, HTTPException, status

from app.a2a_client import A2ATaskError, send_a2a_task
from app.config import get_settings
from app.deps import require_tech_lead
from app.schemas.profile import Profile
from app.schemas.technology import NewTechnologyRequest, Technology
from app.supabase_client import get_admin_client
from app.tracing import new_trace_id

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


@router.post("/technologies", status_code=status.HTTP_201_CREATED)
async def create_technology(
    body: NewTechnologyRequest,
    _profile: Profile = Depends(require_tech_lead),
) -> Technology:
    """Da de alta una tecnología en el catálogo (change `generacion-tecnologias`,
    capacidad technology-catalog: "Alta de tecnologías por el tech lead"). El
    alta pasa por el agente validador antes de guardarse (fail-closed): solo se
    inserta si el veredicto es afirmativo. Rechaza duplicados ignorando
    mayúsculas y espacios sobrantes (409)."""
    admin = get_admin_client()

    # Comprobación de duplicado case-insensitive (design.md D3): `ilike` sin
    # comodines es una comparación exacta que ignora mayúsculas.
    existing = (
        admin.table("technology")
        .select("id")
        .ilike("name", body.name)
        .limit(1)
        .execute()
        .data
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="la tecnologia ya existe en el catalogo",
        )

    settings = get_settings()
    try:
        result = await send_a2a_task(
            settings.agent_validator_url,
            {"technologies": [body.name], "context": "catalog_entry"},
            trace_id=new_trace_id(),
        )
    except A2ATaskError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"el agente validador ha fallado: {exc}",
        ) from exc

    if not result.get("valid"):
        reason = result.get("reason") or "no parece una tecnologia de programacion"
        # Duplicado semantico (change validador-duplicados-tecnologias): el
        # validador detecto que esta entrada ya esta cubierta por una
        # tecnologia existente del catalogo con otro nombre, variante o
        # abreviatura. Se trata como el mismo tipo de conflicto que el
        # duplicado exacto comprobado mas arriba (409), no como una entrada
        # invalida (422).
        if result.get("duplicate_technologies"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=reason)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=reason)

    inserted = admin.table("technology").insert({"name": body.name}).execute().data[0]
    return Technology(**inserted)