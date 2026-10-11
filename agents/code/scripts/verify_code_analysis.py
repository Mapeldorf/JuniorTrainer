"""Verificacion manual de la tarea 4.3: analisis real de un repo con el modelo.

Uso (desde agents/code/, con LITELLM_MASTER_KEY en el .env de la raiz del
repo, LiteLLM corriendo y accesible):
    python -m scripts.verify_code_analysis <repo_path> <tecnologia> [<tecnologia> ...]

Por ejemplo, usando el propio repo de JuniorTrainer como repo de prueba
(no hace falta clonar nada aparte):
    python -m scripts.verify_code_analysis ../web FastAPI LangChain
"""

import asyncio
import logging
import sys

from app.service import analyze_repo

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Uso: python -m scripts.verify_code_analysis <repo_path> <tecnologia> [<tecnologia> ...]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    repo_path = sys.argv[1]
    technologies = sys.argv[2:]

    result = await analyze_repo(repo_path, technologies)

    print(f"memory_hit: {result.memory_hit}")
    print(f"\nresumen:\n{result.summary}")
    print(f"\ntecnologias detectadas: {result.technologies}")
    print(f"\nfragmentos ({len(result.fragments)}):")
    for fragment in result.fragments:
        lines = fragment.code.count("\n") + 1
        print(f"  - {fragment.file}:{fragment.start_line} ({lines} lineas) -- {fragment.note}")
        print(f"    {fragment.code!r}")

    assert result.summary.strip(), "el resumen no deberia estar vacio"
    assert len(result.fragments) <= 10, "no deberian ser mas de 10 fragmentos"
    for fragment in result.fragments:
        assert fragment.code.count("\n") + 1 <= 12, f"fragmento de {fragment.file} tiene mas de 12 lineas"

    print("\nOK: analyze_repo() devolvio resumen, tecnologias y fragmentos dentro de los limites")


if __name__ == "__main__":
    asyncio.run(main())
