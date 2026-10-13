"""Verificacion manual de la tarea 4.3 (actualizada por `acceso-repo-github-tool`):
analisis real de un repositorio de GitHub con el modelo, leido via API.

Uso (desde agents/code/, con LITELLM_MASTER_KEY y GITHUB_APP_* en el .env
de la raiz del repo, LiteLLM corriendo y accesible, y la GitHub App
instalada en el repo de prueba):
    python -m scripts.verify_code_analysis <owner> <repo> <commit_sha> <tecnologia> [<tecnologia> ...]
"""

import asyncio
import logging
import sys

from app.service import analyze_repo

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    if len(sys.argv) < 5:
        print(
            "Uso: python -m scripts.verify_code_analysis <owner> <repo> <commit_sha> "
            "<tecnologia> [<tecnologia> ...]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    owner, repo, commit_sha = sys.argv[1], sys.argv[2], sys.argv[3]
    technologies = sys.argv[4:]

    result = await analyze_repo(owner, repo, commit_sha, technologies)

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
