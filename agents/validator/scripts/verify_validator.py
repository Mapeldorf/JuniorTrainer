"""Verificacion manual del agente validador de tecnologias.

Comprueba dos cosas:
  1. El pre-filtro determinista rechaza entradas con pinta de dato personal
     o identificador (p. ej. un DNI) sin necesidad de modelo ni de red.
  2. Una entrada de tecnologias reales obtiene un veredicto afirmativo del
     modelo (requiere LiteLLM corriendo y las variables de entorno del
     .env de la raiz: AGENT_VALIDATOR_LITELLM_KEY, VALIDATOR_MODEL,
     VALIDATOR_API_KEY).

Uso (desde agents/validator/, con LiteLLM corriendo):
    python -m scripts.verify_validator
"""

import asyncio
import logging

from app.input import InvalidValidatorInput, find_pii_like
from app.service import validate_technologies

logging.basicConfig(level=logging.INFO)


def check_prefilter() -> None:
    assert find_pii_like(["React", "12345678Z"]) == ["12345678Z"], "DNI no detectado"
    assert find_pii_like(["X1234567L"]) == ["X1234567L"], "NIE no detectado"
    assert find_pii_like(["persona@ejemplo.com"]) == ["persona@ejemplo.com"], "email no detectado"
    assert find_pii_like(["ES9121000418450200051332"]), "IBAN no detectado"
    assert find_pii_like(["React", "FastAPI"]) == [], "falso positivo sobre tecnologias reales"
    try:
        # La ruta de normalizacion del parser tambien aplica el pre-filtro.
        from app.input import _normalize

        _normalize(["React", "12345678Z"])
    except InvalidValidatorInput:
        pass
    else:
        raise AssertionError("_normalize acepto un DNI")
    print("pre-filtro: OK (DNI/NIE/email/IBAN rechazados, tecnologias reales aceptadas)")


async def check_model() -> None:
    result = await validate_technologies(["React", "FastAPI"])
    print(f"modelo: valid={result.valid} reason={result.reason!r}")
    if not result.valid:
        raise AssertionError("el validador rechazo tecnologias reales")


def main() -> None:
    check_prefilter()
    asyncio.run(check_model())


if __name__ == "__main__":
    main()
