from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

from app.config import get_settings


def build_agent_card() -> AgentCard:
    """Agent Card del agente de ejercicios: redacta candidatos a partir de
    los resultados de web y/o codigo.

    Ver `openspec/changes/generacion-ejercicios-agentes/proposal.md` (agente
    Ejercicios), `specs/exercise-generation/spec.md`, `specs/agent-memory/spec.md`
    y design.md "Contrato de entrada/salida del agente de ejercicios".
    """
    settings = get_settings()
    return AgentCard(
        name="juniortrainer-agent-exercises",
        description=(
            "Dados el resultado del agente web y/o del agente de codigo, "
            "un tipo de ejercicio y un numero pedido, redacta entre 1 y 5 "
            "ejercicios candidatos de nivel junior recien incorporado "
            "(un unico concepto, enunciado de maximo 50 palabras, nombre "
            "corto de maximo 8 palabras) sin repetir el tema de uno ya "
            "propuesto o ya guardado para ese tipo."
        ),
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=settings.agent_exercises_url,
                protocol_binding=TransportProtocol.JSONRPC,
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="generar_ejercicios",
                name="Generar ejercicios candidatos",
                description=(
                    "Dado exercise_type (knowledge|debug), count (1-5) y el "
                    "resultado del agente web y/o del agente de codigo, "
                    "consulta hasta 200 ejercicios de ese tipo ya guardados o "
                    "eliminados (para no repetir sus temas) y devuelve "
                    "exactamente count candidatos (nombre de maximo 8 "
                    "palabras, enunciado de nivel junior de maximo 50 "
                    "palabras, codigo de apoyo acotado, respuesta "
                    "esperada) que no repiten ninguno de esos temas."
                ),
                tags=["ejercicios", "generacion"],
                examples=["exercise_type=debug, count=3"],
            )
        ],
    )
