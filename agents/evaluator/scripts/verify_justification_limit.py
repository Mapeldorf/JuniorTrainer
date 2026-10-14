"""Verificacion manual del change `ejercicios-nivel-junior`: la
`justification` que propone `evaluate_answer()` tiene 50 palabras como
maximo y sigue senalando que falta o que esta mal.

El limite se comprueba de forma automatica (falla con codigo de salida
distinto de cero si alguna justificacion lo supera); que la
justificacion siga siendo util en 50 palabras no es verificable en
codigo, asi que este script imprime cada una para juzgarla por lectura.

Usa unos pocos ejemplos fijos (respuesta correcta, incompleta e
incorrecta) para no depender de ningun ejercicio real.

Uso (desde agents/evaluator/, con AGENT_EVALUATOR_LITELLM_KEY/EVALUATOR_MODEL en
el .env de la raiz del repo, LiteLLM corriendo):
    python -m scripts.verify_justification_limit
"""

import asyncio
import logging

from app.service import _MAX_JUSTIFICATION_WORDS, evaluate_answer

logging.basicConfig(level=logging.INFO)

_STATEMENT = (
    "En FastAPI, ¿que hace el decorador @app.post('/items') sobre una "
    "funcion que recibe un parametro `item: Item`?"
)
_CODE = [
    {
        "file": "app/main.py",
        "code": "@app.post('/items')\nasync def create_item(item: Item):\n    return item",
    }
]
_EXPECTED_ANSWER = (
    "Registra una ruta POST en /items; FastAPI valida el body de la "
    "peticion contra el modelo Pydantic Item antes de llamar a la funcion."
)

_CASES = [
    ("correcta", "Registra la ruta POST /items y valida el body contra el modelo Item antes de ejecutar la funcion."),
    ("incompleta", "Es una ruta POST."),
    ("incorrecta", "Es una ruta GET que no valida nada."),
]


async def main() -> None:
    offenders = []
    for label, student_answer in _CASES:
        result = await evaluate_answer(_STATEMENT, _CODE, _EXPECTED_ANSWER, student_answer)
        word_count = len(result.justification.split())
        marker = "OK" if word_count <= _MAX_JUSTIFICATION_WORDS else f"EXCEDE (limite {_MAX_JUSTIFICATION_WORDS})"
        print(f"\n=== respuesta {label} ===")
        print(f"verdict: {result.verdict}")
        print(f"justification ({word_count} palabras, {marker}): {result.justification}")
        if word_count > _MAX_JUSTIFICATION_WORDS:
            offenders.append((label, result.justification))

    if offenders:
        print(f"\nFALLO: {len(offenders)} justificacion(es) superan los {_MAX_JUSTIFICATION_WORDS} palabras.")
        raise SystemExit(1)

    print(f"\nOK: todas las justificaciones cumplen el limite de {_MAX_JUSTIFICATION_WORDS} palabras.")
    print("Revisa por lectura arriba que cada una sigue senalando que falta o que esta mal.")


if __name__ == "__main__":
    asyncio.run(main())
