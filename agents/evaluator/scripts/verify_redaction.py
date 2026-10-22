"""Verificacion de la redaccion de datos personales del agente evaluador.

Change `guardarrailes-por-capas`, requisitos de `specs/pii-redaction/spec.md`.

Comprueba:
  1. El complemento determinista del telefono espanol (`redact_national_phone`)
     marca un numero nacional escrito como se escribe -- con y sin
     separadores-- y NO marca cifras que no tienen forma de telefono nacional.
     Sin red ni servicios: es una funcion pura.
  2. Las cinco entidades de la politica vigente se sustituyen por su marcador
     (requiere los servicios de Presidio levantados).
  3. Contenido tecnico que el conjunto de entidades por defecto del detector
     marcaria como nombre de persona o URL (p. ej. `role.guard.ts`,
     `component.ts`) queda INTACTO, porque la politica vigente no incluye
     esas entidades. Es la regresion que motivo `quitar-url-person-presidio`.
  4. La redaccion es fail-closed: si el detector no responde, se propaga
     `RedactionError` en vez de devolver el texto sin redactar.

Uso (desde agents/evaluator/, con presidio-analyzer y presidio-anonymizer
levantados; la comprobacion 1 no los necesita):
    python -m scripts.verify_redaction

Ejecutandolo desde el host hay que apuntar a los puertos publicados o a los
nombres de servicio accesibles; dentro de la red de Docker los valores por
defecto ya sirven:
    PRESIDIO_ANALYZER_API_BASE=http://localhost:5002 \
    PRESIDIO_ANONYMIZER_API_BASE=http://localhost:5001 \
    python -m scripts.verify_redaction
"""

import asyncio
import logging
import os

from app.config import get_settings
from app.redaction import RedactionError, redact, redact_deterministic, redact_reporting

logging.basicConfig(level=logging.INFO)

_MARKER = "<PHONE_NUMBER>"


def check_deterministic() -> None:
    """Comprobacion 1: el complemento determinista, sin red."""
    debe_marcar = [
        "600123456",
        "600 123 456",
        "600 12 34 56",
        "600-123-456",
        "600.123.456",
        "llama al 912345678 si tienes dudas",
        "+34 600 123 456",  # el prefijo queda delante del marcador
    ]
    for texto in debe_marcar:
        resultado = redact_deterministic(texto)
        assert _MARKER in resultado, f"no se marco el telefono en {texto!r}: {resultado!r}"

    no_debe_marcar = [
        "60012345",  # ocho digitos: no es un telefono nacional
        "6001234567",  # diez digitos: tampoco
        "123456789",  # nueve digitos que empiezan por un digito no valido
        "500123456",  # idem
        "el puerto 8080 y la version 9.0.1",
        "4111 1111 1111 1111",  # tarjeta: la cubre el detector, no este patron
    ]
    for texto in no_debe_marcar:
        resultado = redact_deterministic(texto)
        assert resultado == texto, f"se marco algo que no es un telefono en {texto!r}: {resultado!r}"

    iban = "mi cuenta es ES9121000418450200051332 desde 2019"
    assert "<IBAN_CODE>" in redact_deterministic(iban), "no se marco el IBAN en prosa"

    print(f"1. complemento determinista: OK ({len(debe_marcar)} marcados, {len(no_debe_marcar)} intactos)")


async def check_entities() -> None:
    """Comprobacion 2: las cinco entidades de la politica vigente."""
    casos = {
        "EMAIL_ADDRESS": "escribeme a juan@ejemplo.com cuando puedas",
        "CREDIT_CARD": "pague con la 4111 1111 1111 1111 ayer",
        "IP_ADDRESS": "el servidor responde en 192.168.1.1 siempre",
        "IBAN_CODE": "mi cuenta es ES9121000418450200051332 desde 2019",
        "PHONE_NUMBER": "mi movil con prefijo es +34 600 123 456",
    }
    for entidad, texto in casos.items():
        resultado = await redact(texto)
        assert f"<{entidad}>" in resultado, (
            f"{entidad} no se sustituyo en {texto!r}: {resultado!r}"
        )
    print(f"2. entidades de la politica: OK ({len(casos)} sustituidas)")


async def check_code_content_untouched() -> None:
    """Comprobacion 3: la regresion de `quitar-url-person-presidio`.

    Si la redaccion dejara de pedir las entidades explicitamente, el detector
    marcaria estas rutas como PERSON y URL y este caso fallaria."""
    casos = [
        "el guard esta en src/app/core/role.guard.ts y usa component.ts",
        "revisa X.service.ts antes de tocar app.module.ts",
        "importa desde @angular/core y mira package.json",
    ]
    for texto in casos:
        resultado = await redact(texto)
        assert resultado == texto, (
            f"se redacto contenido tecnico en {texto!r}: {resultado!r} -- "
            "comprueba que la llamada al detector sigue pidiendo la lista "
            "explicita de entidades"
        )
    print(f"3. contenido tecnico intacto: OK ({len(casos)} casos)")


async def check_fail_closed() -> None:
    """Comprobacion 4: fail-closed si el detector no responde."""
    originales = {
        "PRESIDIO_ANALYZER_API_BASE": os.environ.get("PRESIDIO_ANALYZER_API_BASE"),
        "PRESIDIO_ANONYMIZER_API_BASE": os.environ.get("PRESIDIO_ANONYMIZER_API_BASE"),
    }
    # Puerto cerrado en localhost: falla rapido y sin depender de DNS.
    os.environ["PRESIDIO_ANALYZER_API_BASE"] = "http://127.0.0.1:1"
    os.environ["PRESIDIO_ANONYMIZER_API_BASE"] = "http://127.0.0.1:1"
    get_settings.cache_clear()
    try:
        texto = "escribeme a juan@ejemplo.com"
        try:
            resultado = await redact(texto)
        except RedactionError:
            print("6. fail-closed: OK (se propago RedactionError con el detector caido)")
            return
        raise AssertionError(
            "con el detector caido se devolvio texto en vez de fallar: "
            f"{resultado!r}. Eso es fail-open y supone enviar el dato sin redactar"
        )
    finally:
        for clave, valor in originales.items():
            if valor is None:
                os.environ.pop(clave, None)
            else:
                os.environ[clave] = valor
        get_settings.cache_clear()


async def check_counter() -> None:
    """Comprobacion 5: el informe de entidades que alimenta la metrica.

    `redact_reporting` devuelve los TIPOS redactados, nunca los valores. Es
    la fuente del contador de activacion de la redaccion, que existe porque
    la red equivalente del proxy no es contable: LiteLLM no registra nada
    cuando enmascara, ni siquiera a nivel DEBUG (comprobado)."""
    _, entidades = await redact_reporting(
        "escribeme a juan@ejemplo.com, al 600123456 o a mi cuenta ES9121000418450200051332 gracias"
    )
    for esperada in ("EMAIL_ADDRESS", "PHONE_NUMBER", "IBAN_CODE"):
        assert esperada in entidades, f"{esperada} no figura en el informe: {entidades}"

    _, vacio = await redact_reporting("el guard esta en src/app/core/role.guard.ts y usa component.ts")
    assert vacio == [], f"se informo de entidades sobre contenido tecnico: {vacio}"

    _, nada = await redact_reporting("   ")
    assert nada == [], "un texto en blanco no deberia informar de nada"
    print("5. contador de activacion: OK (informa tipos, no valores; silencio sin PII)")


def main() -> None:
    check_deterministic()
    asyncio.run(check_entities())
    asyncio.run(check_code_content_untouched())
    asyncio.run(check_counter())
    asyncio.run(check_fail_closed())
    print("\nTodas las comprobaciones han pasado.")


if __name__ == "__main__":
    main()
