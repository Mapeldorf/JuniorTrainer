"""Consulta al detector de PII en la ADMISION de la peticion del validador.

Requisito "Deteccion de PII en modo de bloqueo en el validador" de
`specs/pii-redaction/spec.md` y "Guardarrailes de bloqueo en las llamadas del
validador" de `specs/technology-validation/spec.md` (change
`guardarrailes-por-capas`).

Por que en la admision y no en el proxy. Antes, el rechazo por dato personal
lo hacia un guardarrail del proxy en modo bloqueo, dos capas por debajo de
donde se toma la decision. En la admision solo se puede rechazar -- todavia no
hay prompt que transformar--, y eso es exactamente lo que se quiere aqui: un
nombre de tecnologia con un dato personal dentro no es una tecnologia, es un
error o un ataque. Hacerlo aqui ademas no cuesta ni un token: la peticion se
rechaza antes de construir ninguna llamada al modelo.

Complementa al pre-filtro de expresiones regulares de `app/input.py`, no lo
sustituye, porque cada uno cubre lo que el otro no:

  - el regex cubre **DNI y NIE**, que el detector no reconoce;
  - el detector cubre **tarjeta e IP**, que el regex no detecta.

Comprobado ejecutando `find_pii_like` sobre ambos vectores: una tarjeta y una
IP atraviesan el pre-filtro sin que salte.

Fail-closed: si el detector no responde, se propaga el fallo y la generacion
queda en error, como cualquier otro fallo del validador (requisito "Fallo del
validador es fatal para la generacion"). No se admite la entrada por no poder
comprobarla.
"""

from __future__ import annotations

import httpx

from app.config import get_settings
from app.input import InvalidValidatorInput

# Misma politica de entidades que la redaccion de evaluador y revisor. Se
# piden explicitamente: con el conjunto por defecto el detector marca como
# nombre de persona o URL cualquier ruta o identificador de codigo.
_ENTITIES = ["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IP_ADDRESS", "IBAN_CODE"]

# La imagen por defecto del analizador solo trae reconocedores en ingles: una
# llamada con `language: es` responde 500. Es inocuo para estas entidades, que
# son expresion regular y digito de control.
_LANGUAGE = "en"

_TIMEOUT_SECONDS = 10.0


class PiiDetectionError(RuntimeError):
    """El detector de PII no pudo comprobar la entrada. Se propaga: nunca se
    admite una entrada que no se ha podido comprobar."""


async def find_detectable_pii(technologies: list[str]) -> list[str]:
    """Entradas en las que el detector encuentra algun dato personal.

    Una entrada por llamada, para poder senalar cual es la que sobra en el
    mensaje de rechazo. El numero de llamadas esta acotado por el limite de
    tecnologias de la propia admision, y el detector es local."""
    settings = get_settings()
    analyzer = settings.presidio_analyzer_api_base.rstrip("/")
    offending: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            for technology in technologies:
                response = await client.post(
                    f"{analyzer}/analyze",
                    json={"text": technology, "language": _LANGUAGE, "entities": _ENTITIES},
                )
                response.raise_for_status()
                if response.json():
                    offending.append(technology)
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        raise PiiDetectionError(
            f"no se pudo comprobar la entrada con el detector de PII: {exc}"
        ) from exc

    return offending


async def reject_if_pii_detected(technologies: list[str]) -> None:
    """Rechaza la peticion si el detector encuentra un dato personal.

    Lanza `InvalidValidatorInput`, la misma excepcion que el pre-filtro de
    expresiones regulares, para que el rechazo siga exactamente el mismo
    camino que ya existia."""
    offending = await find_detectable_pii(technologies)
    if offending:
        raise InvalidValidatorInput(
            "la entrada contiene datos que parecen personales o identificadores, "
            f"no tecnologias: {offending!r}"
        )
