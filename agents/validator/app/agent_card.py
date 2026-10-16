from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

from app.config import get_settings


def build_agent_card() -> AgentCard:
    """Agent Card del agente validador de tecnologias: decide si las
    tecnologias de una generacion son tecnologias de programacion antes de
    que arranque el resto del flujo.

    Ver `openspec/changes/validacion-tecnologias-agente-juez/proposal.md`
    y `specs/technology-validation/spec.md`."""
    settings = get_settings()
    return AgentCard(
        name="juniortrainer-agent-validator",
        description=(
            "Dada la lista de tecnologias de una generacion, decide si son "
            "tecnologias relacionadas con la programacion. Politica "
            "default-deny: solo aprueba si todas son tecnologias claramente "
            "reconocibles."
        ),
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=settings.agent_validator_url,
                protocol_binding=TransportProtocol.JSONRPC,
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="validar_tecnologias",
                name="Validar tecnologias de una generacion",
                description=(
                    "Dada una lista de tecnologias, devuelve un veredicto "
                    "estructurado (valid/reason/invalid_technologies) sobre "
                    "si todas son tecnologias de programacion."
                ),
                tags=["validacion", "tecnologias"],
                examples=['technologies=["React", "FastAPI"]'],
            )
        ],
    )
