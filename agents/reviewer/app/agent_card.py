from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

from app.config import get_settings


def build_agent_card() -> AgentCard:
    """Agent Card del agente revisor: revisa la justificacion que el
    agente evaluador propone para el veredicto de una respuesta.

    Ver `openspec/changes/valoracion-respuestas/proposal.md` (agente
    revisor), `specs/answer-evaluation/spec.md` y design.md "Contrato de
    entrada/salida de los agentes"."""
    settings = get_settings()
    return AgentCard(
        name="juniortrainer-agent-reviewer",
        description=(
            "Dados el enunciado, la respuesta de un alumno y el "
            "verdict+justification propuestos por el agente evaluador, "
            "devuelve la justificacion final (confirmada o corregida). "
            "No cambia el verdict."
        ),
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=settings.agent_reviewer_url,
                protocol_binding=TransportProtocol.JSONRPC,
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="revisar_justificacion",
                name="Revisar una justificacion",
                description=(
                    "Dado el enunciado, la respuesta del alumno, y el "
                    "verdict+justification del evaluador, devuelve la "
                    "justificacion final revisada, de maximo 50 "
                    "palabras (acortandola si llegaba mas larga)."
                ),
                tags=["evaluacion", "revision"],
                examples=["statement=..., verdict=correct, justification=..."],
            )
        ],
    )
