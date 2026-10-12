from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

from app.config import get_settings


def build_agent_card() -> AgentCard:
    """Agent Card del agente web: busca documentacion de tecnologias con Tavily.

    Ver `openspec/changes/generacion-ejercicios-agentes/proposal.md` (agente
    Web) y `specs/exercise-generation/spec.md`.
    """
    settings = get_settings()
    return AgentCard(
        name="juniortrainer-agent-web",
        description=(
            "Busca documentacion actual de las tecnologias indicadas y "
            "devuelve un resumen por tecnologia con sus fuentes."
        ),
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=settings.agent_web_url,
                protocol_binding=TransportProtocol.JSONRPC,
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="investigar_tecnologias",
                name="Investigar tecnologias",
                description=(
                    "Dada una lista de tecnologias, busca su documentacion "
                    "actual (hasta 5 busquedas) y devuelve un resumen por "
                    "tecnologia junto con las fuentes encontradas. Si ya se "
                    "buscaron las mismas tecnologias antes, reutiliza el "
                    "resultado guardado sin volver a buscar."
                ),
                tags=["busqueda", "tecnologias"],
                examples=["React, FastAPI", "Kubernetes"],
            )
        ],
    )
