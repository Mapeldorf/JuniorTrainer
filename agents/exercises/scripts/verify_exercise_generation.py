"""Verificacion manual de la tarea 5.3: generate_exercises() devuelve
exactamente `count` candidatos con los cuatro campos (type, statement,
code, expected_answer).

Usa un `web_result`/`code_result` de prueba fijos (no hace falta un
repo real ni Tavily) para aislar lo que se esta probando aqui: la
llamada real al modelo `generator` via LiteLLM. `search_saved_exercises`
tambien se llama de verdad (rol agents_exercise_reader) -- si todavia no
hay ningun ejercicio guardado en Supabase, simplemente no encuentra nada
y sigue igual (no es un fallo).

Uso (desde agents/exercises/, con LITELLM_MASTER_KEY/AGENTS_PG_*/
AGENTS_EXERCISE_READER_PASSWORD/SUPABASE_PROJECT_REF en el .env de la
raiz del repo, LiteLLM corriendo):
    python -m scripts.verify_exercise_generation <knowledge|debug> <count>

Por ejemplo:
    python -m scripts.verify_exercise_generation debug 3
"""

import asyncio
import logging
import sys

from app.service import generate_exercises

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


async def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Uso: python -m scripts.verify_exercise_generation <knowledge|debug> <count>",
            file=sys.stderr,
        )
        raise SystemExit(1)

    exercise_type = sys.argv[1]
    count = int(sys.argv[2])

    result = await generate_exercises(exercise_type, count, _WEB_RESULT, _CODE_RESULT)

    print(f"memory_hit: {result.memory_hit}")
    print(f"candidatos devueltos: {len(result.candidates)} (pedidos: {count})")
    for i, c in enumerate(result.candidates, start=1):
        print(f"\n--- candidato {i} ---")
        print(f"type: {c.type}")
        print(f"statement: {c.statement}")
        print(f"code ({len(c.code)} bloques):")
        for block in c.code:
            print(f"  [{block.file}] {block.code!r}")
        print(f"expected_answer: {c.expected_answer}")

    assert len(result.candidates) == count, f"se pidieron {count} y se recibieron {len(result.candidates)}"
    for c in result.candidates:
        assert c.type == exercise_type
        assert c.statement.strip()
        assert c.expected_answer.strip()

    print(f"\nOK: generate_exercises() devolvio exactamente {count} candidatos con los 4 campos esperados")


if __name__ == "__main__":
    asyncio.run(main())
