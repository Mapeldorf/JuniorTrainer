from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

from app.config import get_settings


def build_agent_card() -> AgentCard:
    """Agent Card del agente evaluador: decide si la respuesta de un
    alumno a un ejercicio es correcta, incompleta o incorrecta.

    Ver `openspec/changes/valoracion-respuestas/proposal.md` (agente
    evaluador), `specs/answer-evaluation/spec.md` y design.md "Contrato
    de entrada/salida de los agentes"."""
    settings = get_settings()
    return AgentCard(
        name="juniortrainer-agent-evaluator",
        description=(
            "Dado un ejercicio (enunciado, codigo de apoyo, respuesta "
            "esperada) y la respuesta de un alumno, decide si es "
            "correcta, incompleta o incorrecta, con una justificacion."
        ),
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=settings.agent_evaluator_url,
                protocol_binding=TransportProtocol.JSONRPC,
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="evaluar_respuesta",
                name="Evaluar una respuesta de alumno",
                description=(
                    "Dado el enunciado, el codigo de apoyo, la respuesta "
                    "esperada (si existe) y la respuesta del alumno, "
                    "devuelve un verdict (correct/incomplete/incorrect) "
                    "y una justificacion."
                ),
                tags=["evaluacion", "respuestas"],
                examples=["statement=..., student_answer=..."],
            )
        ],
    )
