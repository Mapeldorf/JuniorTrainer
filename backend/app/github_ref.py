"""Validacion de `owner`/`repo` (tarea 2.3).

Requisito de `specs/github-repo-access/spec.md` ("Referencia de entrada
del repositorio"): solo caracteres alfanumericos y guiones, sin `/`, `..`
ni espacios -- la misma regla de nombres de usuario/repo de GitHub. Se
aplica ANTES de construir ninguna URL (mitigacion de SSRF, ver
"Host de la API fijo, sin URLs de usuario").
"""

import re

_OWNER_OR_REPO_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$")


class InvalidGitHubRef(ValueError):
    """`owner` o `repo` no cumple el formato permitido."""


def validate_owner_or_repo(value: str, *, field: str) -> str:
    value = value.strip()
    if not _OWNER_OR_REPO_PATTERN.fullmatch(value):
        raise InvalidGitHubRef(
            f"{field} solo puede contener letras, numeros y guiones: {value!r}"
        )
    return value
