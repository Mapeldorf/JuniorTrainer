"""Logica de negocio del agente de codigo, separada del transporte A2A.

Progresion por tarea (ver tasks.md del change `generacion-ejercicios-agentes`):
  - 4.1/4.2: scaffold + `list_files`/`read_file` (ver app/tools/filesystem.py).
  - 4.3 (este fichero, ahora): dos llamadas al modelo `generator` via
    LiteLLM -- una para ELEGIR hasta 10 ficheros relevantes a partir del
    listado del repo, y otra para ANALIZARLOS y producir resumen,
    tecnologias detectadas y fragmentos. No es un bucle agentico con
    tool-calling (mas simple y mas facil de probar); el modelo decide una
    vez que leer, no fichero a fichero.
  - 4.4: memoria larga (todavia no implementada aqui).
  - 4.5: trace_id de Langfuse (todavia no implementada aqui).
"""

import json
import logging
from dataclasses import dataclass, field

from app.llm import build_generator_model
from app.tools.filesystem import FileBudget, FileBudgetExceeded, PathEscapesRepo, list_files, read_file

logger = logging.getLogger(__name__)

# Cuantas entradas del listado de ficheros se le mandan al modelo para que
# elija -- un repo real (p. ej. el de Pokemon de la prueba de aceptacion,
# grupo 8) puede tener miles de ficheros (assets, sprites...); mandarlos
# todos desperdiciaria contexto en algo que el modelo va a ignorar.
_MAX_FILES_IN_LISTING = 500

_PICK_SYSTEM_PROMPT = (
    "Eres un asistente que elige que ficheros de un repositorio merece la "
    "pena leer para preparar ejercicios de programacion sobre unas "
    "tecnologias concretas. Se te da la lista de ficheros del repositorio "
    "(ruta relativa y tamano en bytes) y las tecnologias de interes. Elige "
    "HASTA 10 ficheros, los mas representativos del uso real de esas "
    "tecnologias -- evita ficheros de configuracion vacios, tests "
    "triviales, ficheros generados o binarios. Responde EXCLUSIVAMENTE con "
    "un array JSON de rutas relativas, copiadas tal cual de la lista "
    "recibida, sin explicaciones ni texto alrededor. Ejemplo de respuesta: "
    '["src/App.jsx", "src/hooks/useAuth.js"]'
)

_ANALYZE_SYSTEM_PROMPT = (
    "Eres un asistente que prepara material de referencia para crear "
    "ejercicios de programacion a partir de codigo real. Se te da el "
    "contenido de varios ficheros de un repositorio y las tecnologias de "
    "interes. Responde EXCLUSIVAMENTE con un objeto JSON con tres campos: "
    '"summary" (resumen breve, 3-5 frases, de que hace el repo y como usa '
    'esas tecnologias), "technologies" (array de tecnologias detectadas '
    "REALMENTE en el codigo leido -- pueden coincidir o no con las de "
    'interes), "fragments" (array de hasta 10 fragmentos relevantes, cada '
    'uno con "file" (ruta relativa tal cual se recibio), "start_line" '
    "(entero, numero de linea 1-indexado donde empieza el fragmento en el "
    'fichero original), "code" (como mucho 12 lineas de codigo copiadas '
    'tal cual del fichero, sin inventar nada), "note" (una frase sobre que '
    "ilustra ese fragmento). No inventes contenido que no este en el "
    "codigo proporcionado; si no hay nada relevante que fragmentar, "
    '"fragments" puede quedar vacio.'
)


class CodeAnalysisError(RuntimeError):
    """El modelo no devolvio una respuesta utilizable (JSON invalido, etc.)."""


@dataclass
class CodeFragment:
    file: str
    start_line: int
    code: str
    note: str


@dataclass
class CodeAnalysisResult:
    summary: str
    technologies: list[str] = field(default_factory=list)
    fragments: list[CodeFragment] = field(default_factory=list)
    memory_hit: bool = False


async def analyze_repo(repo_path: str, technologies: list[str]) -> CodeAnalysisResult:
    if not technologies:
        raise ValueError("se necesita al menos una tecnologia")

    entries = list_files(repo_path)
    if not entries:
        raise ValueError(f"el repositorio en {repo_path!r} no tiene ningun fichero legible")

    chosen_paths = await _pick_files(entries, technologies)

    budget = FileBudget(max_calls=10)
    contents: dict[str, str] = {}
    for path in chosen_paths[:10]:
        try:
            contents[path] = read_file(repo_path, path, budget)
        except FileBudgetExceeded:
            break
        except (PathEscapesRepo, FileNotFoundError, OSError):
            # El modelo alucino una ruta que no existe, o escapa del repo
            # (no deberia, viene del propio listado, pero no nos fiamos):
            # se salta ese fichero en vez de fallar la tarea entera.
            logger.warning("no se pudo leer %r elegido por el modelo", path, exc_info=True)
            continue

    if not contents:
        raise CodeAnalysisError(
            "no se pudo leer ningun fichero de los elegidos por el modelo"
        )

    analysis = await _analyze(contents, technologies)
    return CodeAnalysisResult(
        summary=analysis["summary"],
        technologies=analysis["technologies"],
        fragments=[CodeFragment(**f) for f in analysis["fragments"]],
        memory_hit=False,
    )


async def _pick_files(entries, technologies: list[str]) -> list[str]:
    model = build_generator_model()

    listing = "\n".join(f"- {e.path} ({e.size_bytes} bytes)" for e in entries[:_MAX_FILES_IN_LISTING])
    omitted = len(entries) - _MAX_FILES_IN_LISTING
    if omitted > 0:
        listing += f"\n... ({omitted} ficheros mas, omitidos por espacio)"

    human_prompt = (
        f"Tecnologias de interes: {', '.join(technologies)}\n\n"
        f"Ficheros del repositorio:\n{listing}"
    )
    response = await model.ainvoke(
        [
            {"role": "system", "content": _PICK_SYSTEM_PROMPT},
            {"role": "user", "content": human_prompt},
        ]
    )
    paths = _parse_json(response.content, expect=list)
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        raise CodeAnalysisError(f"el modelo no devolvio una lista de rutas valida: {response.content!r}")
    return paths


async def _analyze(contents: dict[str, str], technologies: list[str]) -> dict:
    model = build_generator_model()

    blocks = []
    for path, text in contents.items():
        numbered = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(text.splitlines()))
        blocks.append(f"### {path}\n{numbered}")

    human_prompt = (
        f"Tecnologias de interes: {', '.join(technologies)}\n\n"
        "Contenido de los ficheros elegidos (numeros de linea a la "
        "izquierda, no forman parte del codigo):\n\n" + "\n\n".join(blocks)
    )
    response = await model.ainvoke(
        [
            {"role": "system", "content": _ANALYZE_SYSTEM_PROMPT},
            {"role": "user", "content": human_prompt},
        ]
    )
    data = _parse_json(response.content, expect=dict)
    for key in ("summary", "technologies", "fragments"):
        if key not in data:
            raise CodeAnalysisError(f"falta '{key}' en la respuesta del modelo: {response.content!r}")
    return data


def _parse_json(raw: str, *, expect: type):
    """Parsea la respuesta del modelo como JSON, tolerando que la envuelva
    en una valla de markdown (```json ... ```) a pesar de que el prompt
    pide JSON puro -- algunos modelos lo hacen de todas formas."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CodeAnalysisError(f"el modelo no devolvio JSON valido: {raw!r}") from exc
    if not isinstance(data, expect):
        raise CodeAnalysisError(f"se esperaba un {expect.__name__}, se recibio: {raw!r}")
    return data
