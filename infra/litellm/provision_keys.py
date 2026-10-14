"""Aprovisiona las 5 virtual keys de LiteLLM, una por agente (propuesta
litellm-virtual-keys). Idempotente por `key_alias`: si una key con ese
alias ya existe, se deja intacta y no se genera una nueva (evita invalidar
en caliente un .env ya configurado si se re-ejecuta el script sin querer).
Para rotar una key a proposito, revocarla primero (/key/delete o la UI de
LiteLLM) y volver a ejecutar este script.

Uso (contra un proxy LiteLLM ya levantado, p. ej. `docker compose up
litellm-db litellm`):

    LITELLM_MASTER_KEY=... python infra/litellm/provision_keys.py

Variables de entorno:
    LITELLM_MASTER_KEY  Credencial de administracion del proxy (obligatoria).
    LITELLM_BASE_URL    URL del proxy. Por defecto http://localhost:4000
                         (el puerto que docker-compose.yml publica al host).
"""

from __future__ import annotations

import os
import sys

import httpx

# alias -> modelos logicos permitidos (ver infra/litellm/config.yaml
# model_list y design.md de litellm-virtual-keys).
_AGENT_MODELS: dict[str, list[str]] = {
    "agent-web": ["generator"],
    "agent-code": ["generator"],
    "agent-exercises": ["generator"],
    "agent-evaluator": ["evaluator"],
    "agent-reviewer": ["reviewer"],
}

# alias -> variable de entorno que el agente correspondiente lee
# (agents/*/app/config.py).
_AGENT_ENV_VAR: dict[str, str] = {
    "agent-web": "AGENT_WEB_LITELLM_KEY",
    "agent-code": "AGENT_CODE_LITELLM_KEY",
    "agent-exercises": "AGENT_EXERCISES_LITELLM_KEY",
    "agent-evaluator": "AGENT_EVALUATOR_LITELLM_KEY",
    "agent-reviewer": "AGENT_REVIEWER_LITELLM_KEY",
}


def _key_exists(client: httpx.Client, alias: str) -> bool:
    # /key/info exige el valor real de la key (no el alias) como parametro;
    # /key/list si soporta filtrar por key_alias y devuelve una lista vacia
    # (no 404) cuando no hay ninguna key con ese alias.
    response = client.get("/key/list", params={"key_alias": alias})
    response.raise_for_status()
    return response.json()["total_count"] > 0


def _generate_key(client: httpx.Client, alias: str, models: list[str]) -> str:
    response = client.post(
        "/key/generate",
        json={"key_alias": alias, "models": models},
    )
    response.raise_for_status()
    return response.json()["key"]


def main() -> int:
    master_key = os.environ.get("LITELLM_MASTER_KEY")
    if not master_key:
        print("Error: falta LITELLM_MASTER_KEY en el entorno.", file=sys.stderr)
        return 1

    base_url = os.environ.get("LITELLM_BASE_URL", "http://localhost:4000")

    with httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {master_key}"},
        timeout=30.0,
    ) as client:
        for alias, models in _AGENT_MODELS.items():
            env_var = _AGENT_ENV_VAR[alias]
            if _key_exists(client, alias):
                print(f"{env_var}: ya existe (alias {alias!r}), omitida")
                continue
            key = _generate_key(client, alias, models)
            print(f"{env_var}={key}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
