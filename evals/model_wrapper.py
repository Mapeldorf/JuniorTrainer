"""Dobles y envoltorio del modelo de los agentes.

Los agentes llaman a `model.ainvoke(messages, extra_body=...)` y leen
`.content` de la respuesta. Este modulo ofrece:

  - `ScriptedModel`: doble guionizado (modo simulado). Devuelve, en orden, las
    respuestas crudas del guion del caso, sin red ni credenciales.
  - `RecordingModel`: envoltorio comun (modo simulado y real). Cuenta las
    llamadas, mide el tiempo, guarda el primer prompt y distingue un rechazo
    del proxy por guardarrail de un fallo del modelo. De aqui salen, sin tocar
    el agente, la tasa de reintento correctivo (mas de una llamada), la
    latencia y la comprobacion de delimitadores.

Solo biblioteca estandar.
"""

import time
from types import SimpleNamespace


class ScriptExhausted(RuntimeError):
    """El agente pidio mas llamadas al modelo de las que el guion del caso
    preveia: el codigo del agente ya no se comporta como el caso describe."""


class ScriptedModel:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._next = 0

    async def ainvoke(self, messages, **kwargs):
        if self._next >= len(self._responses):
            raise ScriptExhausted(
                f"el guion tiene {len(self._responses)} respuesta(s) y el agente pidio la numero {self._next + 1}"
            )
        content = self._responses[self._next]
        self._next += 1
        return SimpleNamespace(content=content)


def is_guardrail_rejection(exc: BaseException) -> bool:
    """El proxy LiteLLM rechaza una llamada bloqueada por un guardarrail con
    un error HTTP cuyo mensaje nombra el guardarrail; un fallo del modelo
    (timeout, JSON roto, etc.) no lo hace."""
    return "guardrail" in str(exc).lower()


def extract_usage(response) -> dict | None:
    """Tokens y coste de una respuesta, o `None` si no los trae (los dobles del
    modo simulado no los traen).

    Los tokens salen de `usage_metadata` (con los de razonamiento aparte) y, si
    faltan, de `response_metadata.token_usage`. El coste facturado lo informa
    OpenRouter en `token_usage.cost`, con el desglose de entrada y salida en
    `cost_details`; lo que el proveedor no informe queda `None`, nunca cero.
    """
    usage = getattr(response, "usage_metadata", None) or {}
    metadata = getattr(response, "response_metadata", None) or {}
    token_usage = metadata.get("token_usage") or {}
    input_tokens = usage.get("input_tokens", token_usage.get("prompt_tokens"))
    output_tokens = usage.get("output_tokens", token_usage.get("completion_tokens"))
    if input_tokens is None and output_tokens is None:
        return None
    reasoning = (usage.get("output_token_details") or {}).get("reasoning")
    if reasoning is None:
        reasoning = (token_usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
    details = token_usage.get("cost_details") or {}
    return {
        "input_tokens": int(input_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "reasoning_tokens": None if reasoning is None else int(reasoning),
        "cost": token_usage.get("cost"),
        "prompt_cost": details.get("upstream_inference_prompt_cost"),
        "completion_cost": details.get("upstream_inference_completions_cost"),
    }


def _sum_optional(values: list) -> float | int | None:
    """Suma los valores informados; `None` si ninguno lo esta."""
    present = [v for v in values if v is not None]
    return sum(present) if present else None


class RecordingModel:
    def __init__(self, inner) -> None:
        self._inner = inner
        self.calls = 0
        self.first_messages: list[dict] | None = None
        # Contenido de cada respuesta y prompt de usuario de cada llamada, en
        # orden: el agente de codigo hace dos llamadas distintas (elegir
        # ficheros y analizarlos) y sus metricas salen de ambas.
        self.responses: list[str] = []
        self.user_prompts: list[str] = []
        self.usages: list[dict | None] = []
        self.guardrail_blocked = False
        self.elapsed_seconds = 0.0

    async def ainvoke(self, messages, **kwargs):
        self.calls += 1
        if self.first_messages is None:
            self.first_messages = [dict(m) for m in messages]
        for message in reversed(messages):
            if message.get("role") == "user":
                self.user_prompts.append(str(message.get("content", "")))
                break
        started = time.perf_counter()
        try:
            response = await self._inner.ainvoke(messages, **kwargs)
            self.responses.append(str(getattr(response, "content", "")))
            self.usages.append(extract_usage(response))
            return response
        except Exception as exc:
            if is_guardrail_rejection(exc):
                self.guardrail_blocked = True
            raise
        finally:
            self.elapsed_seconds += time.perf_counter() - started

    def usage_total(self) -> dict | None:
        """Suma de tokens y coste de todas las llamadas del caso, o `None` si
        ninguna informo uso. `cost_complete` es falso si alguna llamada con uso
        no informo su coste: el total seria entonces un minimo."""
        reported = [u for u in self.usages if u is not None]
        if not reported:
            return None
        return {
            "calls": len(reported),
            "input_tokens": sum(u["input_tokens"] for u in reported),
            "output_tokens": sum(u["output_tokens"] for u in reported),
            "reasoning_tokens": _sum_optional([u["reasoning_tokens"] for u in reported]),
            "cost": _sum_optional([u["cost"] for u in reported]),
            "prompt_cost": _sum_optional([u["prompt_cost"] for u in reported]),
            "completion_cost": _sum_optional([u["completion_cost"] for u in reported]),
            "cost_complete": all(u["cost"] is not None for u in reported),
        }

    def first_user_message(self) -> str | None:
        if not self.first_messages:
            return None
        for message in self.first_messages:
            if message.get("role") == "user":
                return str(message.get("content", ""))
        return None
