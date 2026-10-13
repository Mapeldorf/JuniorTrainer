"""Verificacion manual del change `ejercicios-nivel-junior`: los
enunciados de `generate_exercises()` son de nivel junior (un unico
concepto, sin redisenos ni refactors) y de 50 palabras como maximo.

El limite de palabras se comprueba de forma automatica (falla con
codigo de salida distinto de cero si algun enunciado lo supera); el
nivel junior y el unico concepto no son verificables en codigo (ver
design.md decision 4), asi que este script imprime cada enunciado con
su codigo de apoyo para juzgarlos por lectura.

Usa un `web_result`/`code_result` de prueba fijos, igual que
`verify_exercise_generation.py`, para aislar la llamada real al modelo
`generator` via LiteLLM.

Uso (desde agents/exercises/, con LITELLM_MASTER_KEY/AGENTS_PG_*/
AGENTS_EXERCISE_READER_PASSWORD/SUPABASE_PROJECT_REF en el .env de la
raiz del repo, LiteLLM corriendo):
    python -m scripts.verify_statement_limit
"""

import asyncio
import logging

from app.service import _MAX_STATEMENT_WORDS, generate_exercises

logging.basicConfig(level=logging.INFO)

_WEB_RESULT = {
    "summary": (
        "## FastAPI\nFramework web asincrono de Python basado en type hints. "
        "Usa Pydantic para validar entrada/salida y genera documentacion "
        "OpenAPI automaticamente. Las rutas se definen con decoradores "
        "(@app.get, @app.post) y soportan inyeccion de dependencias via Depends()."
    ),
    "sources": [],
    "memory_hit": False,
}

_CODE_RESULT = {
    "summary": "El repo expone una API FastAPI con un endpoint que valida un body con Pydantic.",
    "technologies": ["FastAPI"],
    "fragments": [
        {
            "file": "app/main.py",
            "start_line": 10,
            "code": "@app.post('/items')\nasync def create_item(item: Item):\n    return item",
            "note": "endpoint POST con validacion automatica del body via Pydantic",
        }
    ],
    "memory_hit": False,
}

_COUNT = 3


async def _check_type(exercise_type: str) -> list[str]:
    """Lanza una generacion real de `exercise_type` e imprime cada
    candidato. Devuelve la lista de enunciados que superan el limite
    (vacia si todos cumplen)."""
    result = await generate_exercises(exercise_type, _COUNT, _WEB_RESULT, _CODE_RESULT)

    print(f"\n=== {exercise_type} ({len(result.candidates)} candidatos, pedidos {_COUNT}) ===")
    offenders = []
    for i, c in enumerate(result.candidates, start=1):
        word_count = len(c.statement.split())
        marker = "OK" if word_count <= _MAX_STATEMENT_WORDS else f"EXCEDE (limite {_MAX_STATEMENT_WORDS})"
        print(f"\n--- candidato {i} ({word_count} palabras, {marker}) ---")
        print(f"statement: {c.statement}")
        print(f"code ({len(c.code)} bloques):")
        for block in c.code:
            print(f"  [{block.file}] {block.code!r}")
        print(f"expected_answer: {c.expected_answer}")
        if word_count > _MAX_STATEMENT_WORDS:
            offenders.append(c.statement)

    return offenders


async def main() -> None:
    offenders: list[str] = []
    offenders += await _check_type("knowledge")
    offenders += await _check_type("debug")

    if offenders:
        print(f"\nFALLO: {len(offenders)} enunciado(s) superan los {_MAX_STATEMENT_WORDS} palabras:")
        for s in offenders:
            print(f"  - {s!r} ({len(s.split())} palabras)")
        raise SystemExit(1)

    print(f"\nOK: todos los enunciados cumplen el limite de {_MAX_STATEMENT_WORDS} palabras.")
    print("Revisa por lectura arriba que cada candidato trata un unico concepto y es de nivel junior.")


if __name__ == "__main__":
    asyncio.run(main())
