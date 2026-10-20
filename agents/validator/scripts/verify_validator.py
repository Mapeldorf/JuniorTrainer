"""Verificacion manual del agente validador de tecnologias.

Comprueba:
  1. El pre-filtro determinista rechaza entradas con pinta de dato personal
     o identificador (p. ej. un DNI) sin necesidad de modelo ni de red.
  2. El parseo de la respuesta del modelo (`_parse_result`) aplica
     correctamente la coherencia defensiva de `duplicate_technologies`, sin
     necesidad de modelo ni de red (change `validador-duplicados-tecnologias`).
  3. Un fallo al consultar el catalogo de tecnologias se propaga como fallo
     fatal de la tarea, sin interpretarse como "sin duplicados", sin
     necesidad de base de datos real (se simula con monkeypatch).
  4. Una entrada de tecnologias reales obtiene un veredicto afirmativo del
     modelo, y una entrada que ya esta cubierta por el catalogo (p. ej. la
     abreviatura "TS" de "TypeScript", sembrada por
     `0009_technology_catalog.sql`) se rechaza como duplicado semantico
     (requiere LiteLLM y la base de datos de desarrollo corriendo, y las
     variables de entorno del .env de la raiz: AGENT_VALIDATOR_LITELLM_KEY,
     VALIDATOR_MODEL, VALIDATOR_API_KEY, AGENTS_PG_HOST,
     AGENTS_VALIDATOR_READER_PASSWORD, SUPABASE_PROJECT_REF).

Uso (desde agents/validator/, con LiteLLM y la base de datos corriendo):
    python -m scripts.verify_validator
"""

import asyncio
import json
import logging

import app.service as service_module
from app.input import InvalidValidatorInput, find_pii_like
from app.models import DuplicateTechnology
from app.service import ValidatorError, _parse_result, validate_technologies

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


def check_parse_result_duplicates() -> None:
    valid_no_duplicates = _parse_result(
        json.dumps(
            {
                "valid": True,
                "reason": "ok",
                "invalid_technologies": [],
                "duplicate_technologies": [],
            }
        )
    )
    assert valid_no_duplicates.valid is True
    assert valid_no_duplicates.duplicate_technologies == []

    with_duplicate = _parse_result(
        json.dumps(
            {
                "valid": False,
                "reason": "TS ya esta en el catalogo como TypeScript",
                "invalid_technologies": [],
                "duplicate_technologies": [{"input": "TS", "matches": "TypeScript"}],
            }
        )
    )
    assert with_duplicate.valid is False
    assert with_duplicate.duplicate_technologies == [
        DuplicateTechnology(input="TS", matches="TypeScript")
    ], "duplicate_technologies no se parseo como se esperaba"

    # Coherencia defensiva: valid=true con duplicate_technologies no vacio
    # se trata como no valido (mismo criterio que invalid_technologies).
    incoherent = _parse_result(
        json.dumps(
            {
                "valid": True,
                "reason": "incoherente a proposito",
                "invalid_technologies": [],
                "duplicate_technologies": [{"input": "TS", "matches": "TypeScript"}],
            }
        )
    )
    assert incoherent.valid is False, "la coherencia defensiva no corrigio el valid=true incoherente"

    try:
        _parse_result(json.dumps({"valid": True, "reason": "ok", "invalid_technologies": []}))
    except ValidatorError:
        pass
    else:
        raise AssertionError("una respuesta sin duplicate_technologies deberia fallar el esquema")

    print("parseo de duplicate_technologies: OK (vacio, con coincidencia, coherencia defensiva, esquema incompleto)")


async def check_catalog_failure_is_fatal() -> None:
    async def _boom() -> list[str]:
        raise RuntimeError("fallo simulado de conexion al catalogo")

    original = service_module.list_catalog_technologies
    service_module.list_catalog_technologies = _boom
    try:
        await validate_technologies(["React"])
    except RuntimeError as exc:
        assert "fallo simulado" in str(exc)
    else:
        raise AssertionError(
            "un fallo al consultar el catalogo deberia propagarse, no devolver un veredicto"
        )
    finally:
        service_module.list_catalog_technologies = original
    print("fallo del catalogo: OK (se propaga, no se trata como 'sin duplicados')")


async def check_model() -> None:
    result = await validate_technologies(["React", "FastAPI"])
    print(f"modelo: valid={result.valid} reason={result.reason!r}")
    if not result.valid:
        raise AssertionError("el validador rechazo tecnologias reales")


async def check_duplicate_detection() -> None:
    # "TS" no esta en el catalogo con ese nombre exacto, pero es la
    # abreviatura obvia de "TypeScript" (sembrada por
    # 0009_technology_catalog.sql): el validador debe rechazarla como
    # duplicado semantico, no como tecnologia invalida.
    result = await validate_technologies(["TS"])
    print(
        f"duplicado semantico: valid={result.valid} "
        f"duplicate_technologies={result.duplicate_technologies!r}"
    )
    if result.valid or not result.duplicate_technologies:
        raise AssertionError("el validador no detecto 'TS' como duplicado de 'TypeScript'")

    # Una tecnologia real que no esta en el catalogo no debe marcarse como
    # duplicada (evita falsos positivos).
    no_duplicate = await validate_technologies(["Rust"])
    if no_duplicate.duplicate_technologies:
        raise AssertionError("falso positivo: 'Rust' no deberia coincidir con el catalogo")


def main() -> None:
    check_prefilter()
    check_parse_result_duplicates()
    asyncio.run(check_catalog_failure_is_fatal())
    asyncio.run(check_model())
    asyncio.run(check_duplicate_detection())


if __name__ == "__main__":
    main()
