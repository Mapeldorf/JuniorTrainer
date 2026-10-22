"""Verificacion manual del agente validador de tecnologias.

Comprueba:
  1. El pre-filtro determinista rechaza entradas con pinta de dato personal
     o identificador (p. ej. un DNI) sin necesidad de modelo ni de red.
  2. El parseo de la respuesta del modelo (`_parse_result`) aplica
     correctamente la coherencia defensiva de `duplicate_technologies`, sin
     necesidad de modelo ni de red (change `validador-duplicados-tecnologias`).
  3. El parseo del contexto de la llamada (`parse_context`) cae a
     `"catalog_entry"` ante ausencia o valor desconocido, y solo reconoce
     `"generation"` cuando viene explicito (change `validador-contexto-generacion`),
     sin necesidad de modelo ni de red.
  4. En contexto `"generation"`, `validate_technologies` NO consulta el
     catalogo de tecnologias (se simula con monkeypatch); en contexto
     `"catalog_entry"` SI lo consulta -- mismo comportamiento que antes de
     este change.
  5. Un fallo al consultar el catalogo en contexto `"catalog_entry"` se
     propaga como fallo fatal de la tarea, sin interpretarse como "sin
     duplicados", sin necesidad de base de datos real (se simula con
     monkeypatch).
  6. Una entrada de tecnologias reales obtiene un veredicto afirmativo del
     modelo, y una entrada que ya esta cubierta por el catalogo (p. ej. la
     abreviatura "TS" de "TypeScript", sembrada por
     `0009_technology_catalog.sql`) se rechaza como duplicado semantico en
     contexto `"catalog_entry"` (requiere LiteLLM y la base de datos de
     desarrollo corriendo, y las variables de entorno del .env de la raiz:
     AGENT_VALIDATOR_LITELLM_KEY, VALIDATOR_MODEL, VALIDATOR_API_KEY,
     AGENTS_PG_HOST, AGENTS_VALIDATOR_READER_PASSWORD, SUPABASE_PROJECT_REF).
  7. Esa misma tecnologia ya existente ("TypeScript") obtiene un veredicto
     afirmativo en contexto `"generation"`: NO se rechaza como "duplicado de
     si misma" (caso real que motivo el change `validador-contexto-generacion`),
     requiere LiteLLM pero no la base de datos (no se consulta el catalogo).

Uso (desde agents/validator/, con LiteLLM y la base de datos corriendo):
    python -m scripts.verify_validator
"""

import asyncio
import json
import logging

from a2a.helpers.proto_helpers import new_data_message

import app.service as service_module
from app.input import InvalidValidatorInput, find_pii_like, parse_context
from app.pii import reject_if_pii_detected
from app.models import DuplicateTechnology
from app.service import ValidatorError, _parse_result, validate_technologies

logging.basicConfig(level=logging.INFO)


def _data_message(data: dict):
    """Mismo tipo de `Message` que recibe `ValidatorAgentExecutor.execute`,
    con una unica parte de datos -- `parse_context` lee la parte de datos
    con `get_data_parts`, que exige un `Message` real del SDK, no un doble."""
    return new_data_message(data)


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
        ),
        check_duplicates=True,
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
        ),
        check_duplicates=True,
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
        ),
        check_duplicates=True,
    )
    assert incoherent.valid is False, "la coherencia defensiva no corrigio el valid=true incoherente"

    try:
        _parse_result(
            json.dumps({"valid": True, "reason": "ok", "invalid_technologies": []}),
            check_duplicates=True,
        )
    except ValidatorError:
        pass
    else:
        raise AssertionError("una respuesta sin duplicate_technologies deberia fallar el esquema")

    # Contexto `generation` (change `validador-contexto-generacion`): el
    # esquema simplificado no exige `duplicate_technologies`, y el resultado
    # lo deja vacio sin fallar.
    simplified = _parse_result(
        json.dumps({"valid": True, "reason": "ok", "invalid_technologies": []}),
        check_duplicates=False,
    )
    assert simplified.valid is True
    assert simplified.duplicate_technologies == []

    print(
        "parseo de duplicate_technologies: OK (vacio, con coincidencia, coherencia "
        "defensiva, esquema incompleto en catalog_entry, esquema simplificado en generation)"
    )


def check_parse_context() -> None:
    assert parse_context(_data_message({"context": "generation"})) == "generation"
    assert parse_context(_data_message({"context": "catalog_entry"})) == "catalog_entry"
    assert parse_context(_data_message({})) == "catalog_entry", "sin context deberia caer a catalog_entry"
    assert (
        parse_context(_data_message({"context": "algo-desconocido"})) == "catalog_entry"
    ), "un valor no reconocido deberia caer a catalog_entry"
    print("parseo de context: OK (generation, catalog_entry, ausente y desconocido)")


async def check_catalog_queried_only_in_catalog_entry() -> None:
    calls: list[str] = []

    async def _tracking_catalog() -> list[str]:
        calls.append("called")
        return ["React"]

    original = service_module.list_catalog_technologies
    service_module.list_catalog_technologies = _tracking_catalog
    try:
        await validate_technologies(["React"], context="generation")
        assert calls == [], "el catalogo no deberia consultarse en contexto generation"
        await validate_technologies(["React"], context="catalog_entry")
        assert calls == ["called"], "el catalogo deberia consultarse en contexto catalog_entry"
    finally:
        service_module.list_catalog_technologies = original
    print("consulta al catalogo: OK (omitida en generation, hecha en catalog_entry)")


async def check_catalog_failure_is_fatal() -> None:
    async def _boom() -> list[str]:
        raise RuntimeError("fallo simulado de conexion al catalogo")

    original = service_module.list_catalog_technologies
    service_module.list_catalog_technologies = _boom
    try:
        await validate_technologies(["React"], context="catalog_entry")
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
    result = await validate_technologies(["React", "FastAPI"], context="catalog_entry")
    print(f"modelo: valid={result.valid} reason={result.reason!r}")
    if not result.valid:
        raise AssertionError("el validador rechazo tecnologias reales")


async def check_duplicate_detection() -> None:
    # "TS" no esta en el catalogo con ese nombre exacto, pero es la
    # abreviatura obvia de "TypeScript" (sembrada por
    # 0009_technology_catalog.sql): en contexto catalog_entry (alta) el
    # validador debe rechazarla como duplicado semantico, no como
    # tecnologia invalida.
    result = await validate_technologies(["TS"], context="catalog_entry")
    print(
        f"duplicado semantico (catalog_entry): valid={result.valid} "
        f"duplicate_technologies={result.duplicate_technologies!r}"
    )
    if result.valid or not result.duplicate_technologies:
        raise AssertionError("el validador no detecto 'TS' como duplicado de 'TypeScript'")

    # Una tecnologia real que no esta en el catalogo no debe marcarse como
    # duplicada (evita falsos positivos).
    no_duplicate = await validate_technologies(["Rust"], context="catalog_entry")
    if no_duplicate.duplicate_technologies:
        raise AssertionError("falso positivo: 'Rust' no deberia coincidir con el catalogo")


async def check_generation_skips_duplicate_check() -> None:
    # Caso real que motivo el change `validador-contexto-generacion`:
    # "TypeScript" ya esta en el catalogo (sembrada por
    # 0009_technology_catalog.sql) con ese nombre EXACTO. En contexto
    # generation no se compara contra el catalogo, asi que no se rechaza
    # como "duplicado de si misma".
    result = await validate_technologies(["TypeScript"], context="generation")
    print(f"generation sobre tecnologia ya existente: valid={result.valid} reason={result.reason!r}")
    if not result.valid:
        raise AssertionError(
            "en contexto generation, una tecnologia ya existente en el catalogo "
            "no deberia rechazarse (se estaria tratando como duplicado de si misma)"
        )
    if result.duplicate_technologies:
        raise AssertionError("duplicate_technologies deberia quedar vacio en contexto generation")


async def check_admission_pii_detection() -> None:
    """Rechazo por PII en la admision (change `guardarrailes-por-capas`).

    Complementa al pre-filtro de regex, no lo repite: los dos vectores de
    aqui -- una tarjeta y una IP-- ATRAVIESAN el regex (lo comprueba la
    primera assert), y es el detector el que los para. Al reves, el DNI lo
    para el regex y el detector no lo conoce. Requiere los servicios de
    Presidio levantados."""
    tarjeta, ip = "4111 1111 1111 1111", "192.168.1.1"

    assert find_pii_like([tarjeta]) == [], "el regex ya para la tarjeta: este caso ya no prueba el detector"
    assert find_pii_like([ip]) == [], "el regex ya para la IP: este caso ya no prueba el detector"

    for valor in (tarjeta, ip):
        try:
            await reject_if_pii_detected(["React", valor])
        except InvalidValidatorInput:
            continue
        raise AssertionError(f"la admision no rechazo {valor!r}, que el detector si reconoce")

    # Tecnologias reales no deben rechazarse.
    await reject_if_pii_detected(["React", "FastAPI", "PostgreSQL"])
    print("admision con detector de PII: OK (tarjeta e IP rechazadas, tecnologias reales admitidas)")


def main() -> None:
    check_prefilter()
    asyncio.run(check_admission_pii_detection())
    check_parse_result_duplicates()
    check_parse_context()
    asyncio.run(check_catalog_queried_only_in_catalog_entry())
    asyncio.run(check_catalog_failure_is_fatal())
    asyncio.run(check_model())
    asyncio.run(check_duplicate_detection())
    asyncio.run(check_generation_skips_duplicate_check())


if __name__ == "__main__":
    main()
