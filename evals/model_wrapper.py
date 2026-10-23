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


class RecordingModel:
    def __init__(self, inner) -> None:
        self._inner = inner
        self.calls = 0
        self.first_messages: list[dict] | None = None
        self.guardrail_blocked = False
        self.elapsed_seconds = 0.0

    async def ainvoke(self, messages, **kwargs):
        self.calls += 1
        if self.first_messages is None:
            self.first_messages = [dict(m) for m in messages]
        started = time.perf_counter()
        try:
            return await self._inner.ainvoke(messages, **kwargs)
        except Exception as exc:
            if is_guardrail_rejection(exc):
                self.guardrail_blocked = True
            raise
        finally:
            self.elapsed_seconds += time.perf_counter() - started

    def first_user_message(self) -> str | None:
        if not self.first_messages:
            return None
        for message in self.first_messages:
            if message.get("role") == "user":
                return str(message.get("content", ""))
        return None
