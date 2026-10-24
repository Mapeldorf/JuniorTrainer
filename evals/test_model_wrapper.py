"""Tests del doble guionizado y del envoltorio del modelo.

Uso (desde la raiz del repo): python -m unittest evals.test_model_wrapper
"""

import asyncio
import unittest

from types import SimpleNamespace

from evals.model_wrapper import (
    RecordingModel,
    ScriptedModel,
    ScriptExhausted,
    extract_usage,
    is_guardrail_rejection,
)


def reply(content="ok", input_tokens=10, output_tokens=5, reasoning=2, cost=0.001, prompt_cost=0.0004,
          completion_cost=0.0006):
    """Respuesta con la forma que devuelve `langchain-openai` a traves de LiteLLM."""
    token_usage = {"prompt_tokens": input_tokens, "completion_tokens": output_tokens}
    if cost is not None:
        token_usage["cost"] = cost
        token_usage["cost_details"] = {"upstream_inference_prompt_cost": prompt_cost,
                                       "upstream_inference_completions_cost": completion_cost}
    return SimpleNamespace(
        content=content,
        usage_metadata={"input_tokens": input_tokens, "output_tokens": output_tokens,
                        "output_token_details": {"reasoning": reasoning}},
        response_metadata={"token_usage": token_usage},
    )


class FixedReplies:
    def __init__(self, replies):
        self._replies = list(replies)

    async def ainvoke(self, messages, **kwargs):
        return self._replies.pop(0)


def run(coro):
    return asyncio.run(coro)


class UsageTests(unittest.TestCase):
    def test_extrae_tokens_razonamiento_y_coste(self):
        usage = extract_usage(reply())
        self.assertEqual(usage, {"input_tokens": 10, "output_tokens": 5, "reasoning_tokens": 2,
                                 "cost": 0.001, "prompt_cost": 0.0004, "completion_cost": 0.0006})

    def test_sin_coste_informado_queda_none_y_no_cero(self):
        usage = extract_usage(reply(cost=None))
        self.assertEqual(usage["input_tokens"], 10)
        self.assertIsNone(usage["cost"])
        self.assertIsNone(usage["prompt_cost"])

    def test_el_doble_del_modo_simulado_no_trae_uso(self):
        self.assertIsNone(extract_usage(SimpleNamespace(content="x")))

    def test_tokens_desde_token_usage_si_falta_usage_metadata(self):
        response = SimpleNamespace(content="x", usage_metadata=None,
                                   response_metadata={"token_usage": {"prompt_tokens": 7, "completion_tokens": 3}})
        usage = extract_usage(response)
        self.assertEqual((usage["input_tokens"], usage["output_tokens"]), (7, 3))
        self.assertIsNone(usage["reasoning_tokens"])

    def test_varias_llamadas_suman(self):
        model = RecordingModel(FixedReplies([reply(input_tokens=10, output_tokens=5, cost=0.001),
                                             reply(input_tokens=20, output_tokens=8, cost=0.002)]))
        run(model.ainvoke([{"role": "user", "content": "a"}]))
        run(model.ainvoke([{"role": "user", "content": "b"}]))
        total = model.usage_total()
        self.assertEqual((total["calls"], total["input_tokens"], total["output_tokens"]), (2, 30, 13))
        self.assertAlmostEqual(total["cost"], 0.003)
        self.assertTrue(total["cost_complete"])

    def test_coste_incompleto_si_una_llamada_no_lo_informa(self):
        model = RecordingModel(FixedReplies([reply(cost=0.001), reply(cost=None)]))
        run(model.ainvoke([{"role": "user", "content": "a"}]))
        run(model.ainvoke([{"role": "user", "content": "b"}]))
        total = model.usage_total()
        self.assertAlmostEqual(total["cost"], 0.001)
        self.assertFalse(total["cost_complete"])

    def test_simulado_no_disponible_en_lugar_de_cero(self):
        model = RecordingModel(ScriptedModel(["a"]))
        run(model.ainvoke([{"role": "user", "content": "x"}]))
        self.assertIsNone(model.usage_total())

    def test_sin_llamadas_no_hay_uso(self):
        self.assertIsNone(RecordingModel(ScriptedModel([])).usage_total())


class ScriptedModelTests(unittest.TestCase):
    def test_devuelve_las_respuestas_en_orden(self):
        model = ScriptedModel(["uno", "dos"])
        self.assertEqual(run(model.ainvoke([])).content, "uno")
        self.assertEqual(run(model.ainvoke([])).content, "dos")

    def test_guion_agotado(self):
        model = ScriptedModel(["uno"])
        run(model.ainvoke([]))
        with self.assertRaises(ScriptExhausted):
            run(model.ainvoke([]))


class RecordingModelTests(unittest.TestCase):
    def test_cuenta_llamadas_y_guarda_el_primer_prompt(self):
        model = RecordingModel(ScriptedModel(["a", "b"]))
        first = [{"role": "system", "content": "S"}, {"role": "user", "content": "primer prompt"}]
        second = [*first, {"role": "assistant", "content": "a"}, {"role": "user", "content": "corrige"}]
        run(model.ainvoke(first))
        run(model.ainvoke(second))
        self.assertEqual(model.calls, 2)
        self.assertEqual(model.first_user_message(), "primer prompt")

    def test_guarda_respuestas_y_prompts_de_cada_llamada_en_orden(self):
        model = RecordingModel(ScriptedModel(["r1", "r2"]))
        run(model.ainvoke([{"role": "system", "content": "S"}, {"role": "user", "content": "p1"}]))
        run(model.ainvoke([{"role": "user", "content": "p2"}]))
        self.assertEqual(model.responses, ["r1", "r2"])
        self.assertEqual(model.user_prompts, ["p1", "p2"])

    def test_una_respuesta_fallida_no_se_guarda(self):
        model = RecordingModel(ScriptedModel([]))
        with self.assertRaises(ScriptExhausted):
            run(model.ainvoke([{"role": "user", "content": "p"}]))
        self.assertEqual(model.responses, [])
        self.assertEqual(model.user_prompts, ["p"])

    def test_una_sola_llamada_no_es_reintento(self):
        model = RecordingModel(ScriptedModel(["a"]))
        run(model.ainvoke([{"role": "user", "content": "x"}]))
        self.assertEqual(model.calls, 1)

    def test_sin_llamadas(self):
        model = RecordingModel(ScriptedModel([]))
        self.assertEqual(model.calls, 0)
        self.assertIsNone(model.first_user_message())

    def test_distingue_rechazo_de_guardarrail(self):
        class Blocked:
            async def ainvoke(self, messages, **kwargs):
                raise RuntimeError("Error code: 400 - Violated guardrail policy: prompt_attack")

        model = RecordingModel(Blocked())
        with self.assertRaises(RuntimeError):
            run(model.ainvoke([{"role": "user", "content": "x"}]))
        self.assertTrue(model.guardrail_blocked)

    def test_un_fallo_normal_no_es_guardarrail(self):
        class Timeout:
            async def ainvoke(self, messages, **kwargs):
                raise TimeoutError("request timed out")

        model = RecordingModel(Timeout())
        with self.assertRaises(TimeoutError):
            run(model.ainvoke([{"role": "user", "content": "x"}]))
        self.assertFalse(model.guardrail_blocked)

    def test_mide_tiempo(self):
        model = RecordingModel(ScriptedModel(["a"]))
        run(model.ainvoke([]))
        self.assertGreaterEqual(model.elapsed_seconds, 0.0)

    def test_heuristica_de_guardarrail(self):
        self.assertTrue(is_guardrail_rejection(RuntimeError("Guardrail blocked the request")))
        self.assertFalse(is_guardrail_rejection(RuntimeError("503 service unavailable")))


if __name__ == "__main__":
    unittest.main()
