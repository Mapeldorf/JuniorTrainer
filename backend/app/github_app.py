"""Cliente de autenticacion de la GitHub App (tarea 2.1).

Patron estandar de GitHub Apps: un JWT firmado con la clave privada de la
App (`RS256`, `iss`=App ID, expiracion corta) se intercambia por un token
de instalacion (`POST /app/installations/{id}/access_tokens`). La
instalacion a usar se resuelve en tiempo de llamada por `owner`/`repo`
(`GET /repos/{owner}/{repo}/installation`), sin un ID de instalacion fijo
en configuracion -- la misma App puede estar instalada en varias
organizaciones/repos.

El token de instalacion se cachea en memoria del proceso hasta ~5 minutos
antes de su expiracion real (GitHub los emite con ~1h de validez), para
no repetir el intercambio en cada llamada de lectura dentro de la misma
generacion.

Requisito de `specs/github-repo-access/spec.md` ("Autenticacion mediante
GitHub App de solo lectura"): toda llamada a la API de GitHub se autentica
con un token de instalacion de esta App.
"""

import time
from datetime import datetime
from functools import lru_cache

import httpx
import jwt

from app.config import get_settings

GITHUB_API_BASE = "https://api.github.com"

# GitHub rechaza un JWT con mas de 10 minutos de vigencia; 9 deja margen
# de reloj sin arriesgarse a ese limite.
_JWT_TTL_SECONDS = 9 * 60
# Margen de renovacion: un token de instalacion a punto de caducar no se
# reutiliza, se pide uno nuevo.
_TOKEN_REFRESH_MARGIN_SECONDS = 5 * 60


class GitHubAppError(RuntimeError):
    """Fallo autenticando contra GitHub o resolviendo la instalacion de la App."""


class GitHubAppClient:
    def __init__(
        self,
        *,
        app_id: str,
        private_key: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._app_id = app_id
        self._private_key = private_key
        self._http = http_client or httpx.AsyncClient(base_url=GITHUB_API_BASE, timeout=10.0)
        self._owns_http = http_client is None
        # owner/repo en minusculas -> (token, epoch de expiracion)
        self._installation_tokens: dict[str, tuple[str, float]] = {}

    def _build_app_jwt(self) -> str:
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + _JWT_TTL_SECONDS, "iss": self._app_id}
        return jwt.encode(payload, self._private_key, algorithm="RS256")

    async def _resolve_installation_id(self, owner: str, repo: str) -> int:
        response = await self._http.get(
            f"/repos/{owner}/{repo}/installation",
            headers={
                "Authorization": f"Bearer {self._build_app_jwt()}",
                "Accept": "application/vnd.github+json",
            },
        )
        if response.status_code == 404:
            raise GitHubAppError(
                f"la GitHub App no esta instalada en {owner}/{repo} (o el repositorio no existe)"
            )
        if response.status_code >= 400:
            raise GitHubAppError(
                f"no se pudo resolver la instalacion de la App para {owner}/{repo}: "
                f"{response.status_code} {response.text}"
            )
        return response.json()["id"]

    async def get_installation_token(self, owner: str, repo: str) -> str:
        """Token de instalacion para `owner`/`repo`, de cache si todavia es valido."""
        cache_key = f"{owner}/{repo}".lower()
        cached = self._installation_tokens.get(cache_key)
        now = time.time()
        if cached is not None and cached[1] - _TOKEN_REFRESH_MARGIN_SECONDS > now:
            return cached[0]

        installation_id = await self._resolve_installation_id(owner, repo)
        response = await self._http.post(
            f"/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {self._build_app_jwt()}",
                "Accept": "application/vnd.github+json",
            },
        )
        if response.status_code >= 400:
            raise GitHubAppError(
                f"no se pudo generar el token de instalacion para {owner}/{repo}: "
                f"{response.status_code} {response.text}"
            )
        data = response.json()
        token = data["token"]
        expires_at = datetime.fromisoformat(data["expires_at"]).timestamp()
        self._installation_tokens[cache_key] = (token, expires_at)
        return token

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()


@lru_cache
def get_github_app_client() -> GitHubAppClient:
    settings = get_settings()
    return GitHubAppClient(app_id=settings.github_app_id, private_key=settings.github_app_private_key)
