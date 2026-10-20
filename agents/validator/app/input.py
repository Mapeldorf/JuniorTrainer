"""Extrae la lista de tecnologias de un mensaje A2A entrante y aplica el
pre-filtro determinista de PII/identificadores.

Acepta dos formas, para que tanto el orquestador programatico como una
llamada manual de depuracion funcionen igual:
  - Parte de datos: {"technologies": ["React", "FastAPI"]}
  - Parte de texto: "React, FastAPI" (separado por comas o saltos de linea)

Limite de numero/longitud: misma revalidacion independiente que ya hace
`agents/web/app/input.py`, aunque `backend/app/schemas/generation.py` ya
aplica el mismo limite antes de llamar a este agente -- no se depende de
que el unico llamador posible siga siendo siempre correcto.

Pre-filtro determinista (change `validacion-tecnologias-agente-juez`): antes
de invocar al modelo se rechaza cualquier entrada que coincida con un
patron de dato personal o identificador (email, telefono, IBAN o documento
nacional de identidad/extranjero), de forma no probabilistica. Cubre el
caso del DNI, que Presidio no detecta (sus entidades son email, telefono,
tarjeta, IP, IBAN).

Contexto de la llamada (change `validador-contexto-generacion`): la parte de
datos puede traer tambien `"context"` (`"catalog_entry"` o `"generation"`,
ver `app/models.py`), que decide si `app/service.py` aplica la comprobacion
de duplicados contra el catalogo. `parse_context` lo extrae con el mismo
criterio fail-safe en los dos sentidos: ausencia o valor no reconocido
siempre caen a `"catalog_entry"` (la comprobacion mas estricta, la que ya
se hacia antes de que existiera este campo)."""

import re

from a2a.helpers.proto_helpers import get_data_parts, get_text_parts
from a2a.types import Message

from app.models import ValidationContext

_MAX_TECHNOLOGIES = 15
_MAX_TECHNOLOGY_LENGTH = 60

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_IBAN_RE = re.compile(r"\b[A-Za-z]{2}\d{2}[A-Za-z0-9]{10,30}\b")
_DNI_RE = re.compile(r"^\d{8}[A-Za-z]$")
_NIE_RE = re.compile(r"^[XYZxyz]\d{7}[A-Za-z]$")
_PHONE_CHARS_RE = re.compile(r"^\+?[\d\s().\-]+$")
_PHONE_DIGITS_RE = re.compile(r"^\d{9,15}$")


class InvalidValidatorInput(ValueError):
    """El mensaje no trae una lista de tecnologias valida: supera los
    limites de numero/longitud, o contiene una entrada con pinta de dato
    personal o identificador."""


def parse_technologies(message: Message) -> list[str]:
    for data in get_data_parts(message.parts):
        if isinstance(data, dict) and isinstance(data.get("technologies"), list):
            return _normalize([str(t) for t in data["technologies"]])

    text = "\n".join(get_text_parts(message.parts))
    if not text.strip():
        return []
    raw = text.replace("\n", ",").split(",")
    return _normalize(raw)


def parse_context(message: Message) -> ValidationContext:
    """Extrae el contexto de la llamada de la parte de datos del mensaje
    (ver cabecera del modulo). Solo la parte de datos puede traerlo -- la
    forma de texto (depuracion manual) no tiene donde ponerlo y siempre cae
    al valor por defecto."""
    for data in get_data_parts(message.parts):
        if isinstance(data, dict) and data.get("context") == "generation":
            return "generation"
    return "catalog_entry"


def _normalize(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        value = item.strip()
        if value and value not in seen:
            seen[value] = None
    result = list(seen)
    if len(result) > _MAX_TECHNOLOGIES:
        raise InvalidValidatorInput(
            f"no se permiten mas de {_MAX_TECHNOLOGIES} tecnologias por peticion"
        )
    too_long = [t for t in result if len(t) > _MAX_TECHNOLOGY_LENGTH]
    if too_long:
        raise InvalidValidatorInput(
            f"cada tecnologia debe tener como maximo {_MAX_TECHNOLOGY_LENGTH} caracteres: {too_long!r}"
        )
    pii_like = find_pii_like(result)
    if pii_like:
        raise InvalidValidatorInput(
            f"la entrada contiene datos que parecen personales o identificadores, no tecnologias: {pii_like!r}"
        )
    return result


def find_pii_like(technologies: list[str]) -> list[str]:
    """Devuelve las entradas que coinciden con un patron de dato personal o
    identificador, para rechazarlas antes de invocar al modelo."""
    return [t for t in technologies if _looks_like_pii(t)]


def _looks_like_pii(text: str) -> bool:
    if _EMAIL_RE.search(text):
        return True
    if _IBAN_RE.search(text):
        return True
    if _DNI_RE.match(text) or _NIE_RE.match(text):
        return True
    return _looks_like_phone(text)


def _looks_like_phone(text: str) -> bool:
    if _PHONE_DIGITS_RE.match(text):
        return True
    digits = re.sub(r"\D", "", text)
    if 9 <= len(digits) <= 15 and _PHONE_CHARS_RE.match(text):
        return True
    return False
