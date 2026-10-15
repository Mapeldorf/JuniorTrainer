"""Aprovisiona las 5 virtual keys de LiteLLM, una por agente (propuesta
litellm-virtual-keys), con un techo de gasto fijo (propuesta
litellm-key-budgets) y un limite de ritmo fijo (propuesta
litellm-key-rate-limit). Idempotente por `key_alias`, con upsert por campo:
    - alias no existe              -> crea la key con todos los campos.
    - alias existe, falta algun campo (max_budget/rpm_limit) -> actualiza
      solo los campos que faltan, en una unica llamada (no la regenera:
      mismo valor de key).
    - alias existe con todos los campos ya puestos -> se deja intacta (no
      pisa un valor que se haya ajustado a mano despues de crearla).
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

# Limite de ritmo por key (propuesta litellm-key-rate-limit): mismo numero
# que ya usa slowapi en cada agente (agents/*/app/rate_limit.py).
_RPM_LIMIT = 60

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
            "rpm_limit": _RPM_LIMIT,
        },
    )
    response.raise_for_status()
    return response.json()["key"]


def _missing_fields(existing: dict) -> dict:
    missing: dict = {}
    if existing.get("max_budget") is None:
        missing["max_budget"] = _MAX_BUDGET_USD
        missing["budget_duration"] = _BUDGET_DURATION
    if existing.get("rpm_limit") is None:
        missing["rpm_limit"] = _RPM_LIMIT
    return missing


def _apply_missing_fields(client: httpx.Client, token: str, fields: dict) -> None:
    response = client.post("/key/update", json={"key": token, **fields})
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
                continue
            missing = _missing_fields(existing)
            if missing:
                _apply_missing_fields(client, existing["token"], missing)
                print(f"{env_var}: ya existia (alias {alias!r}), actualizada con {sorted(missing)}")
            else:
                print(f"{env_var}: ya existe completa (alias {alias!r}), omitida")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
