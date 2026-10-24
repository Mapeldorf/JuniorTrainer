"""Aprovisiona las virtual keys de LiteLLM, una por agente (propuesta
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
    LITELLM_KEY_MAX_BUDGET_USD
                        Techo de gasto por key en USD. Por defecto 5 (desarrollo);
                        en produccion se exporta 50 (el dimensionado del capstone
                        §3.4). Debe ser un numero mayor que 0.
"""

from __future__ import annotations

import os
import sys

import httpx

# alias -> modelos logicos permitidos (ver infra/litellm/config.yaml
# model_list y design.md de litellm-virtual-keys). Incluye el modelo de
# fallback de Hugging Face de cada agente (propuesta
# litellm-huggingface-fallback): sin el en `models`, no hay garantia de que
# LiteLLM deje usar la key en la llamada de fallback.
_AGENT_MODELS: dict[str, list[str]] = {
    "agent-web": ["generator", "generator-fallback-hf"],
    "agent-code": ["generator", "generator-fallback-hf"],
    "agent-exercises": ["generator", "generator-fallback-hf"],
    "agent-evaluator": ["evaluator", "evaluator-fallback-hf"],
    "agent-reviewer": ["reviewer", "reviewer-fallback-hf"],
    "agent-validator": ["validator", "validator-fallback-hf"],
}

# Sin metadata por key (change `guardarrailes-por-capas`). Hubo una:
# `opted_out_global_guardrails` excluia a la key del validador del
# guardarrail GLOBAL `lakera-guard`, porque ese guardarrail enmascaraba la
# PII antes de que el de bloqueo pudiera verla y rechazarla. Al dejar de
# haber guardarrailes globales -- la deteccion de inyeccion se vincula ahora
# por deployment-- no hay nada de lo que excluirse, y el mecanismo entero
# desaparece con su requisito y su verificacion.
#
# Una key existente puede conservar esa metadata de antes: es inerte, porque
# ya no existe el guardarrail global al que se referia.

# Techo de gasto por key. El importe se lee de LITELLM_KEY_MAX_BUDGET_USD
# (change litellm-key-budget-configurable): 5 USD por defecto en desarrollo,
# 50 en produccion (el dimensionado del capstone §3.4). El upsert de abajo
# nunca pisa un budget ya puesto, asi que cambiar la variable no reescribe las
# keys ya aprovisionadas de otro entorno; ver design.md. El periodo es fijo.
_DEFAULT_MAX_BUDGET_USD = 5.0
_MAX_BUDGET_ENV_VAR = "LITELLM_KEY_MAX_BUDGET_USD"
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
    "agent-validator": "AGENT_VALIDATOR_LITELLM_KEY",
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


def _generate_key(
    client: httpx.Client, alias: str, models: list[str], max_budget: float
) -> str:
    body: dict = {
        "key_alias": alias,
        "models": models,
        "max_budget": max_budget,
        "budget_duration": _BUDGET_DURATION,
        "rpm_limit": _RPM_LIMIT,
    }
    response = client.post("/key/generate", json=body)
    response.raise_for_status()
    return response.json()["key"]


def _missing_fields(
    existing: dict, desired_models: list[str], max_budget: float
) -> dict:
    missing: dict = {}
    if existing.get("max_budget") is None:
        missing["max_budget"] = max_budget
        missing["budget_duration"] = _BUDGET_DURATION
    if existing.get("rpm_limit") is None:
        missing["rpm_limit"] = _RPM_LIMIT
    # set() porque el orden de /key/list no tiene por que coincidir con el
    # de _AGENT_MODELS; solo nos importa si falta algun modelo (p. ej. el
    # fallback de litellm-huggingface-fallback en una key ya existente).
    if set(existing.get("models") or []) != set(desired_models):
        missing["models"] = desired_models
    return missing


def _apply_missing_fields(client: httpx.Client, token: str, fields: dict) -> None:
    response = client.post("/key/update", json={"key": token, **fields})
    response.raise_for_status()


def _read_max_budget() -> float:
    """Techo de gasto por key en USD: la variable de entorno o el defecto."""
    raw = os.environ.get(_MAX_BUDGET_ENV_VAR)
    if raw is None or raw.strip() == "":
        return _DEFAULT_MAX_BUDGET_USD
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"{_MAX_BUDGET_ENV_VAR}={raw!r} no es un numero")
    if value <= 0:
        raise ValueError(f"{_MAX_BUDGET_ENV_VAR}={raw!r} debe ser mayor que 0")
    return value


def main() -> int:
    master_key = os.environ.get("LITELLM_MASTER_KEY")
    if not master_key:
        print("Error: falta LITELLM_MASTER_KEY en el entorno.", file=sys.stderr)
        return 1

    try:
        max_budget = _read_max_budget()
    except ValueError as exc:
        print(f"Error: {exc}.", file=sys.stderr)
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
                key = _generate_key(client, alias, models, max_budget)
                print(f"{env_var}={key}")
                continue
            missing = _missing_fields(existing, models, max_budget)
            if missing:
                _apply_missing_fields(client, existing["token"], missing)
                print(f"{env_var}: ya existia (alias {alias!r}), actualizada con {sorted(missing)}")
            else:
                print(f"{env_var}: ya existe completa (alias {alias!r}), omitida")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
