"""Tabla de precios (`evals/prices.json`): carga, consulta y refresco.

Los precios se guardan por millon de tokens, con fecha y fuente, y se refrescan
desde la lista publica de modelos de OpenRouter (sin credenciales). Un modelo
ausente hace fallar el calculo: nunca se supone un precio. Solo biblioteca
estandar.
"""

import json
import urllib.request
from datetime import date
from pathlib import Path

PRICES_PATH = Path(__file__).resolve().parent / "prices.json"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
HUGGINGFACE_MODELS_URL = "https://router.huggingface.co/v1/models"

AGENTS = ("evaluator", "reviewer", "validator", "exercises", "web", "code")


class PriceError(ValueError):
    """Falta un precio o la tabla esta mal formada."""


def load_prices(path: Path = PRICES_PATH) -> dict:
    prices = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("currency", "models", "roles", "tavily", "fallback"):
        if key not in prices:
            raise PriceError(f"prices.json: falta '{key}'")
    for kind in ("production", "reference"):
        roles = prices["roles"].get(kind)
        if not isinstance(roles, dict) or any(agent not in roles for agent in AGENTS):
            raise PriceError(f"prices.json: roles.{kind} debe asignar un modelo a cada agente {AGENTS}")
    return prices


def model_price(prices: dict, model_id: str) -> dict:
    """`{input_per_m, output_per_m}` del modelo; falla si no esta o no tiene precio."""
    entry = prices["models"].get(model_id)
    if entry is None:
        raise PriceError(f"el modelo '{model_id}' no esta en la tabla de precios")
    if entry.get("input_per_m") is None or entry.get("output_per_m") is None:
        raise PriceError(f"el modelo '{model_id}' esta en la tabla pero sin precio: ejecuta el refresco")
    return entry


def agent_model(prices: dict, kind: str, agent: str) -> str:
    """Modelo de un agente: `production` (el que usa hoy) o `reference` (el de comparacion)."""
    return prices["roles"][kind][agent]


def token_cost(prices: dict, model_id: str, input_tokens: float, output_tokens: float) -> float:
    entry = model_price(prices, model_id)
    return (input_tokens * entry["input_per_m"] + output_tokens * entry["output_per_m"]) / 1_000_000


def fallback_price(prices: dict, agent: str, bound: str) -> dict:
    """Precio por millon del modelo de respaldo del agente: `min` es el
    proveedor de inferencia mas barato (entrada + salida) y `max` el mas caro.
    Hugging Face decide el proveedor, asi que se informa el rango."""
    fallback = prices["fallback"]
    model_id = fallback["roles"].get(agent)
    providers = (fallback["models"].get(model_id) or {}).get("providers") or {}
    if not providers:
        raise PriceError(f"el modelo de respaldo '{model_id}' del agente '{agent}' no tiene precios: ejecuta el refresco")
    pick = min if bound == "min" else max
    name = pick(providers, key=lambda p: providers[p]["input_per_m"] + providers[p]["output_per_m"])
    return {"model": model_id, "provider": name, **providers[name]}


def tavily_plan(prices: dict, name: str | None = None) -> dict:
    tavily = prices["tavily"]
    name = name or tavily["selected_plan"]
    plan = tavily["plans"].get(name)
    if plan is None:
        raise PriceError(f"el plan de Tavily '{name}' no esta en la tabla de precios")
    return {"name": name, "credits_per_search": tavily["credits_per_search"], **plan}


def extract_prices(models_response: dict, model_ids: list[str]) -> dict[str, dict]:
    """Precios por millon de tokens de `model_ids` a partir de la respuesta de
    `GET /api/v1/models`. Los modelos que no aparecen se omiten del resultado."""
    by_id = {m["id"]: m for m in models_response.get("data", [])}
    found = {}
    for model_id in model_ids:
        pricing = (by_id.get(model_id) or {}).get("pricing")
        if not pricing or pricing.get("prompt") in (None, "") or pricing.get("completion") in (None, ""):
            continue
        found[model_id] = {
            "input_per_m": round(float(pricing["prompt"]) * 1_000_000, 6),
            "output_per_m": round(float(pricing["completion"]) * 1_000_000, 6),
        }
    return found


def extract_hf_prices(models_response: dict, model_ids: list[str]) -> dict[str, dict]:
    """Precios por millon de tokens de cada proveedor de inferencia de `model_ids`
    segun `GET https://router.huggingface.co/v1/models`; solo proveedores activos
    (`live`) que publican precio."""
    by_id = {m["id"]: m for m in models_response.get("data", [])}
    found = {}
    for model_id in model_ids:
        providers = {}
        for provider in (by_id.get(model_id) or {}).get("providers", []):
            pricing = provider.get("pricing")
            if provider.get("status") == "live" and pricing and pricing.get("input") is not None \
                    and pricing.get("output") is not None:
                providers[provider["provider"]] = {"input_per_m": float(pricing["input"]),
                                                   "output_per_m": float(pricing["output"])}
        if providers:
            found[model_id] = providers
    return found


def fetch_models(url: str = OPENROUTER_MODELS_URL, timeout: float = 30.0) -> dict:
    # Consulta publica de solo lectura: no se envia ninguna credencial.
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def refresh(path: Path = PRICES_PATH, models_response: dict | None = None, today: date | None = None,
            hf_response: dict | None = None) -> dict:
    """Actualiza `models` y, si la tabla lo tiene, los precios por proveedor del
    respaldo (solo los modelos que ya figuran) y la fecha. Devuelve
    `{modelo: (precio_antiguo, precio_nuevo)}` de los que cambian; los del respaldo
    llevan el prefijo `hf:`."""
    path = Path(path)
    prices = load_prices(path)
    response = models_response if models_response is not None else fetch_models(prices.get("source", OPENROUTER_MODELS_URL))
    new = extract_prices(response, list(prices["models"]))
    changes = {}
    for model_id, entry in new.items():
        old = {k: prices["models"][model_id].get(k) for k in ("input_per_m", "output_per_m")}
        if old != entry:
            changes[model_id] = (old, entry)
        prices["models"][model_id].update(entry)
    missing = [m for m in prices["models"] if m not in new]
    prices["fetched"] = (today or date.today()).isoformat()
    fallback = prices.get("fallback")
    if fallback:
        try:
            hf = hf_response if hf_response is not None else fetch_models(fallback.get("source", HUGGINGFACE_MODELS_URL))
        except OSError as exc:
            print(f"AVISO: no se pudo consultar Hugging Face ({exc}); se mantienen los precios del respaldo")
            hf = None
        if hf is not None:
            new_hf = extract_hf_prices(hf, list(fallback["models"]))
            for model_id, providers in new_hf.items():
                old_providers = fallback["models"][model_id].get("providers") or {}
                if old_providers != providers:
                    changes[f"hf:{model_id}"] = (old_providers, providers)
                fallback["models"][model_id]["providers"] = providers
            fallback["fetched"] = prices["fetched"]
            lost = [m for m in fallback["models"] if m not in new_hf]
            if lost:
                print(f"AVISO: sin precios publicados para el respaldo {lost}; se mantienen los que hubiera")
    path.write_text(json.dumps(prices, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if missing:
        print(f"AVISO: sin precio publicado para {missing}; se mantiene el que hubiera")
    return changes
