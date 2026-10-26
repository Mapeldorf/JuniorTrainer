from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import TransportProtocol

from app.config import get_settings


def build_agent_card() -> AgentCard:
    """Agent Card del agente de codigo: lee un repositorio de GitHub por API
    (solo lectura).

    Ver `openspec/changes/generacion-ejercicios-agentes/proposal.md` (agente
    Codigo), `specs/exercise-generation/spec.md` y design.md "Contrato de
    entrada del agente de codigo".
    """
    settings = get_settings()
    return AgentCard(
        name="juniortrainer-agent-code",
        description=(
            "Lee un repositorio de GitHub por API (solo lectura, con la "
            "GitHub App) y devuelve un resumen, las tecnologias detectadas y "
            "fragmentos de codigo relevantes."
        ),
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=settings.agent_code_url,
                protocol_binding=TransportProtocol.JSONRPC,
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="analizar_repositorio",
                name="Analizar repositorio",
                description=(
                    "Dado un repositorio (owner/repo) y su commit_sha y una "
                    "lista de tecnologias de interes, elige y analiza hasta "
                    "10 ficheros -- solo lectura, con las rutas validadas "
                    "contra el arbol real del commit -- y devuelve un "
                    "resumen, las tecnologias detectadas y hasta 10 "
                    "fragmentos de codigo relevantes. Si ya se proceso el "
                    "mismo repositorio (mismo commit) con las mismas "
                    "tecnologias antes, reutiliza el resultado guardado sin "
                    "releer ningun fichero."
                ),
                tags=["codigo", "repositorio"],
                examples=["owner=octocat, repo=pokemon, commit_sha=deadbeef, technologies=React,Redux"],
            )
        ],
    )
