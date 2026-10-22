"""Redaccion de datos personales de los campos escritos por una persona.

Requisitos "Redaccion automatica de PII antes de la llamada al proveedor",
"Redaccion acotada a los campos escritos por una persona", "Cobertura
determinista del telefono nacional" y "Entidades solicitadas de forma
explicita al detector" de `specs/pii-redaction/spec.md` (change
`guardarrailes-por-capas`).

Por que aqui y no en el proxy. El proxy LiteLLM recibe el prompt ya montado,
como una cadena plana, y no puede distinguir la respuesta del alumno del
codigo de apoyo que el sistema adjunta. Redactar ahi obligaba a recortar
entidades y agentes para contener los falsos positivos sobre contenido
tecnico (changes `quitar-url-person-presidio` y
`presidio-solo-evaluador-revisor`). El agente si sabe que campo es cada cosa,
asi que redacta solo el campo escrito por una persona. Y como lo hace antes
de que el prompt salga del proceso, todo destinatario posterior -- el
detector de inyeccion, el proveedor, el proveedor de respaldo y las trazas --
recibe el texto ya limpio, sin depender del orden de ejecucion interno de
LiteLLM.

Dos detalles de la API del detector que condicionan esta implementacion
(design.md decision 10, ambos comprobados contra el servicio real):

  - **Las entidades se piden explicitamente.** Con el conjunto por defecto,
    `src/app/core/role.guard.ts` dispara `PERSON` y `URL`, que son las dos
    entidades retiradas a proposito por falsos positivos masivos sobre
    rutas e identificadores de codigo. Con la lista explicita, ese mismo
    texto no dispara nada.
  - **El idioma es `en`.** La imagen por defecto del analizador solo trae
    reconocedores en ingles: una llamada con `language: es` responde
    `500 No matching recognizers were found`. Es inocuo para estas cinco
    entidades, que son expresion regular y digito de control y no dependen
    del idioma -- con una excepcion, el telefono, que se cubre aparte.

Fail-closed (design.md decision 5): si el detector no responde, la tarea
falla en vez de enviar el texto sin redactar. Es la misma postura que ya
tenia la integracion de Presidio en LiteLLM, y lo contrario convertiria la
caida de un servicio local en una fuga silenciosa.
"""

from __future__ import annotations

import re

import httpx

from app.config import get_settings

# Politica vigente de entidades (change `quitar-url-person-presidio`): las de
# riesgo real que no colisionan con rutas ni identificadores de codigo. URL y
# PERSON estan fuera a proposito; no basta con no nombrarlas, hay que pedir
# esta lista explicitamente (ver cabecera del modulo).
_ENTITIES = ["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IP_ADDRESS", "IBAN_CODE"]

_LANGUAGE = "en"

# Por debajo del timeout de 45s del cliente del modelo: la redaccion ocurre
# antes de la llamada al LLM y no debe comerse su presupuesto.
_TIMEOUT_SECONDS = 10.0

# Telefono espanol sin prefijo internacional (design.md decision 10). El
# reconocedor del detector solo lo encuentra con prefijo (`+34 600 123 456`
# si, `600123456` no), asi que un movil espanol escrito como se escribe no se
# redactaba nunca.
#
# Nueve digitos que empiezan por 6, 7, 8 o 9 -- los digitos iniciales validos
# en Espana-- con separadores opcionales, y sin digitos pegados a los
# extremos para no morder una cifra mas larga. Acotarlo asi evita marcar
# cualquier numero largo de la prosa del alumno; el codigo de apoyo no pasa
# por aqui (solo se redactan los campos escritos por una persona), asi que una
# constante numerica del codigo no se ve afectada.
_NATIONAL_PHONE_RE = re.compile(r"(?<!\d)[6-9](?:[ .\-]?\d){8}(?!\d)")

# IBAN dentro de una frase. El reconocedor del detector solo lo encuentra si
# el IBAN esta al final del texto o seguido de un signo de puntuacion:
# comprobado contra el servicio real, "mi cuenta es ES91...1332" se detecta y
# "mi cuenta es ES91...1332 desde 2019" NO. Como el IBAN si forma parte de la
# politica de entidades, cubrirlo de forma determinista no es alcance
# anadido: es lo que hace que el requisito se cumpla de verdad.
#
# Mismo patron que ya usa el pre-filtro del validador
# (`agents/validator/app/input.py`), por coherencia con lo que el proyecto ya
# da por bueno en produccion.
_IBAN_RE = re.compile(r"\b[A-Za-z]{2}\d{2}[A-Za-z0-9]{10,30}\b")

# Mismo formato de marcador que usa el anonimizador (`<ENTITY_TYPE>`), para
# que el texto redactado sea homogeneo venga de donde venga.
_PHONE_MARKER = "<PHONE_NUMBER>"
_IBAN_MARKER = "<IBAN_CODE>"


class RedactionError(RuntimeError):
    """No se pudo completar la redaccion (el detector no responde o devuelve
    algo inesperado). Se propaga: fail-closed, nunca se envia el texto sin
    redactar."""


def redact_deterministic(text: str) -> str:
    """Complemento determinista de los reconocedores del detector.

    Cubre los dos casos en los que el detector falla sobre texto en prosa: el
    telefono espanol sin prefijo internacional y el IBAN que no esta al final
    de la frase. Separado de `redact` a proposito: es una funcion pura, sin
    red, y por tanto comprobable sin levantar nada."""
    text = _NATIONAL_PHONE_RE.sub(_PHONE_MARKER, text)
    return _IBAN_RE.sub(_IBAN_MARKER, text)


async def redact(text: str) -> str:
    """Devuelve `text` con los datos personales sustituidos por un marcador.

    Se aplica UNICAMENTE a campos escritos por una persona. No llamar con el
    enunciado, el codigo de apoyo ni la respuesta esperada: ese contenido lo
    deriva el sistema de otras fuentes y redactarlo lo corrompe sin aportar
    privacidad a nadie."""
    if not text or not text.strip():
        return text

    settings = get_settings()
    analyzer = settings.presidio_analyzer_api_base.rstrip("/")
    anonymizer = settings.presidio_anonymizer_api_base.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            analysis = await client.post(
                f"{analyzer}/analyze",
                json={"text": text, "language": _LANGUAGE, "entities": _ENTITIES},
            )
            analysis.raise_for_status()
            findings = analysis.json()

            # Sin hallazgos no hay nada que anonimizar: se ahorra la segunda
            # llamada, que con `analyzer_results` vacio devolveria el mismo
            # texto.
            if findings:
                anonymized = await client.post(
                    f"{anonymizer}/anonymize",
                    json={"text": text, "analyzer_results": findings},
                )
                anonymized.raise_for_status()
                text = anonymized.json()["text"]
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise RedactionError(f"no se pudo redactar el texto: {exc}") from exc

    return redact_deterministic(text)
