"""Verificacion manual de los changes `ejercicios-nivel-junior` y
`ejercicios-con-nombre`: los enunciados de `generate_exercises()` son de
nivel junior (un unico concepto, sin redisenos ni refactors) y de 50
palabras como maximo, y cada candidato trae ademas un nombre corto
(distinto del enunciado) de 8 palabras como maximo.

Los dos limites de palabras se comprueban de forma automatica (falla
con codigo de salida distinto de cero si algun enunciado o nombre los
supera); el nivel junior, el unico concepto y si el nombre es una
etiqueta util (no una copia del enunciado) no son verificables en
codigo (ver design.md decision 4 de `ejercicios-nivel-junior`), asi que
este script imprime cada enunciado y nombre con su codigo de apoyo para
juzgarlos por lectura.

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

from app.service import _MAX_NAME_WORDS, _MAX_STATEMENT_WORDS, generate_exercises

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


async def _check_type(exercise_type: str) -> tuple[list[str], list[str]]:
    """Lanza una generacion real de `exercise_type` e imprime cada
    candidato. Devuelve `(enunciados_que_se_pasan, nombres_que_se_pasan)`
    (vacias si todos cumplen)."""
    result = await generate_exercises(exercise_type, _COUNT, _WEB_RESULT, _CODE_RESULT)

    print(f"\n=== {exercise_type} ({len(result.candidates)} candidatos, pedidos {_COUNT}) ===")
    statement_offenders = []
    name_offenders = []
    for i, c in enumerate(result.candidates, start=1):
        name_words = len(c.name.split())
        name_marker = "OK" if name_words <= _MAX_NAME_WORDS else f"EXCEDE (limite {_MAX_NAME_WORDS})"
        statement_words = len(c.statement.split())
        statement_marker = (
            "OK" if statement_words <= _MAX_STATEMENT_WORDS else f"EXCEDE (limite {_MAX_STATEMENT_WORDS})"
        )
        print(f"\n--- candidato {i} ---")
        print(f"name ({name_words} palabras, {name_marker}): {c.name}")
        print(f"statement ({statement_words} palabras, {statement_marker}): {c.statement}")
        print(f"code ({len(c.code)} bloques):")
        for block in c.code:
            print(f"  [{block.file}] {block.code!r}")
        print(f"expected_answer: {c.expected_answer}")
        if statement_words > _MAX_STATEMENT_WORDS:
            statement_offenders.append(c.statement)
        if name_words > _MAX_NAME_WORDS:
            name_offenders.append(c.name)

    return statement_offenders, name_offenders


async def main() -> None:
    statement_offenders: list[str] = []
    name_offenders: list[str] = []
    for exercise_type in ("knowledge", "debug"):
        s_off, n_off = await _check_type(exercise_type)
        statement_offenders += s_off
        name_offenders += n_off

    if statement_offenders or name_offenders:
        if statement_offenders:
            print(f"\nFALLO: {len(statement_offenders)} enunciado(s) superan los {_MAX_STATEMENT_WORDS} palabras:")
            for s in statement_offenders:
                print(f"  - {s!r} ({len(s.split())} palabras)")
        if name_offenders:
            print(f"\nFALLO: {len(name_offenders)} nombre(s) superan las {_MAX_NAME_WORDS} palabras:")
            for n in name_offenders:
                print(f"  - {n!r} ({len(n.split())} palabras)")
        raise SystemExit(1)

    print(
        f"\nOK: todos los enunciados cumplen el limite de {_MAX_STATEMENT_WORDS} palabras "
        f"y todos los nombres cumplen el limite de {_MAX_NAME_WORDS} palabras."
    )
    print(
        "Revisa por lectura arriba que cada candidato trata un unico concepto, es de nivel junior, "
        "y que su nombre es una etiqueta corta y distinta del enunciado (no una copia truncada)."
    )


if __name__ == "__main__":
    asyncio.run(main())
