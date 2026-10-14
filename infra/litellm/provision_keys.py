"""Aprovisiona las 5 virtual keys de LiteLLM, una por agente (propuesta
litellm-virtual-keys), con un techo de gasto fijo (propuesta
litellm-key-budgets). Idempotente por `key_alias`, con upsert de budget:
    - alias no existe          -> crea la key con max_budget/budget_duration.
    - alias existe sin budget  -> actualiza esa key con max_budget/budget_duration
                                   (no la regenera: mismo valor de key).
    - alias existe con budget  -> se deja intacta (no pisa un budget que se
                                   haya ajustado a mano despues de crearla).
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

# Techo de gasto por key (propuesta litellm-key-budgets): mismo importe y
# periodo para las 5, ver design.md para la justificacion.
_MAX_BUDGET_USD = 5
_BUDGET_DURATION = "30d"

# alias -> variable de entorno que el agente correspondiente lee
# (agents/*/app/config.py).
_AGENT_ENV_VAR: dict[str, str] = {
    "agent-web": "AGENT_WEB_LITELLM_KEY",
    "agent-code": "AGENT_CODE_LITELLM_KEY",
    "agent-exercises": "AGENT_EXERCISES_LITELLM_KEY",
    "agent-evaluator": "AGENT_EVALUATOR_LITELLM_KEY",
    "agent-reviewer": "AGENT_REVIEWER_LITELLM_KEY",
}


def _find_key(client: httpx.Client, alias: str) -> dict | None:
    # /key/info exige el valor real de la key (no el alias) como parametro;
    # /key/list si soporta filtrar por key_alias, y con return_full_object
    # trae tambien max_budget sin necesitar el valor real de la key (solo
    # necesitamos `token`, el hash, que /key/update si acepta como `key`).
    response = client.get(
        "/key/list",
        params={"key_alias": alias, "return_full_object": "true"},
    )
    response.raise_for_status()
    keys = response.json()["keys"]
    return keys[0] if keys else None


def _generate_key(client: httpx.Client, alias: str, models: list[str]) -> str:
    response = client.post(
        "/key/generate",
        json={
            "key_alias": alias,
            "models": models,
            "max_budget": _MAX_BUDGET_USD,
            "budget_duration": _BUDGET_DURATION,
        },
    )
    response.raise_for_status()
    return response.json()["key"]


def _apply_budget(client: httpx.Client, token: str) -> None:
    response = client.post(
        "/key/update",
        json={
            "key": token,
            "max_budget": _MAX_BUDGET_USD,
            "budget_duration": _BUDGET_DURATION,
        },
    )
    response.raise_for_status()


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
            existing = _find_key(client, alias)
            if existing is None:
                key = _generate_key(client, alias, models)
                print(f"{env_var}={key}")
            elif existing.get("max_budget") is None:
                _apply_budget(client, existing["token"])
                print(f"{env_var}: ya existia sin budget (alias {alias!r}), actualizada con budget")
            else:
                print(f"{env_var}: ya existe con budget (alias {alias!r}), omitida")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
