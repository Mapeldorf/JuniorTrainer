"""Verificacion manual del change `ejercicios-nivel-junior`: la
justificacion final que devuelve `review_justification()` tiene 50
palabras como maximo, incluso cuando la justificacion propuesta por el
evaluador llega deliberadamente larga.

El limite se comprueba de forma automatica (falla con codigo de salida
distinto de cero si alguna version final lo supera); que siga siendo
coherente con el veredicto no es verificable en codigo, asi que este
script imprime cada una para juzgarla por lectura.

Uso (desde agents/reviewer/, con AGENT_REVIEWER_LITELLM_KEY/REVIEWER_MODEL en
el .env de la raiz del repo, LiteLLM corriendo):
    python -m scripts.verify_justification_limit
"""

import asyncio
import logging

from app.service import _MAX_JUSTIFICATION_WORDS, review_justification

logging.basicConfig(level=logging.INFO)

_STATEMENT = (
    "En FastAPI, ¿que hace el decorador @app.post('/items') sobre una "
    "funcion que recibe un parametro `item: Item`?"
)

_CASES = [
    (
        "justificacion ya corta",
        "correct",
        "Registra la ruta POST /items y valida el body contra el modelo Item antes de ejecutar la funcion.",
    ),
    (
        "justificacion deliberadamente larga",
        "incorrect",
        "La respuesta del alumno confunde el metodo HTTP con GET cuando en realidad el decorador que "
        "aparece en el codigo de apoyo es @app.post, lo cual significa que la ruta solo acepta peticiones "
        "de tipo POST y que, ademas, antes de ejecutar el cuerpo de la funcion create_item, FastAPI valida "
        "automaticamente el contenido del body recibido contra el modelo Pydantic Item declarado como tipo "
        "del parametro item, rechazando la peticion con un error 422 si el body no coincide con ese modelo.",
    ),
]


async def main() -> None:
    offenders = []
    for label, verdict, justification in _CASES:
        result = await review_justification(_STATEMENT, "respuesta de ejemplo del alumno", verdict, justification)
        word_count = len(result.justification.split())
        marker = "OK" if word_count <= _MAX_JUSTIFICATION_WORDS else f"EXCEDE (limite {_MAX_JUSTIFICATION_WORDS})"
        print(f"\n=== {label} (verdict={verdict}) ===")
        print(f"justification propuesta ({len(justification.split())} palabras): {justification}")
        print(f"justification final ({word_count} palabras, {marker}): {result.justification}")
        if word_count > _MAX_JUSTIFICATION_WORDS:
            offenders.append((label, result.justification))

    if offenders:
        print(f"\nFALLO: {len(offenders)} version(es) final(es) superan los {_MAX_JUSTIFICATION_WORDS} palabras.")
        raise SystemExit(1)

    print(f"\nOK: todas las versiones finales cumplen el limite de {_MAX_JUSTIFICATION_WORDS} palabras.")
    print("Revisa por lectura arriba que cada una sigue siendo coherente con su veredicto.")


if __name__ == "__main__":
    asyncio.run(main())
