"""Verificacion manual de la tarea 5.4: una segunda generacion del mismo
tipo no repite el tema de un enunciado ya propuesto (requisito "El agente
de ejercicios no repite temas ya propuestos").

El mecanismo (historial leido, incluido en el prompt, y escrito tras
generar) ya esta autoverificado contra Postgres real sin necesitar el
modelo (ver tasks.md 5.4). Lo que SOLO se puede comprobar con una llamada
real es que el modelo de verdad evita el tema, no solo que el prompt se lo
pida -- para eso es este script: lanza dos generaciones seguidas del
mismo tipo (un tipo nuevo, unico por ejecucion, para no arrastrar
historial de ejecuciones anteriores) y imprime los enunciados de ambas
para que los compares a ojo.

Uso (desde agents/exercises/, con LITELLM_MASTER_KEY/AGENTS_PG_*/
AGENTS_EXERCISE_READER_PASSWORD/SUPABASE_PROJECT_REF en el .env de la
raiz del repo, LiteLLM corriendo):
    python -m scripts.verify_no_repeated_themes
"""

import asyncio
import logging
import uuid

from app.service import generate_exercises

logging.basicConfig(level=logging.INFO)

_WEB_RESULT = {
    "summary": (
        "## Python\nPython es un lenguaje interpretado, de tipado dinamico, "
        "con soporte nativo para programacion orientada a objetos, "
        "funcional y estructurada. Usa indentacion para delimitar bloques."
    ),
    "sources": [],
    "memory_hit": False,
}


async def main() -> None:
    exercise_type = f"debug-verify-{uuid.uuid4().hex[:8]}"

    result1 = await generate_exercises(exercise_type, 2, _WEB_RESULT, None)
    print(f"1a generacion: memory_hit={result1.memory_hit}")
    for c in result1.candidates:
        print(f"  - {c.statement}")

    result2 = await generate_exercises(exercise_type, 2, _WEB_RESULT, None)
    print(f"\n2a generacion: memory_hit={result2.memory_hit}")
    for c in result2.candidates:
        print(f"  - {c.statement}")

    assert result1.memory_hit is False, "la primera generacion de un tipo nuevo no deberia tener historial"
    assert result2.memory_hit is True, "la segunda deberia ver el historial de la primera"

    print()
    print(
        "OK (mecanico): memory_hit paso de false a true. Revisa a ojo los "
        "enunciados de arriba: los de la 2a generacion NO deberian tratar "
        "el mismo tema que los de la 1a (aunque usen otras palabras)."
    )


if __name__ == "__main__":
    asyncio.run(main())
