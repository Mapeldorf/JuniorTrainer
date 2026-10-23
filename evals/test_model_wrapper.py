"""Tests del doble guionizado y del envoltorio del modelo.

Uso (desde la raiz del repo): python -m unittest evals.test_model_wrapper
"""

import asyncio
import unittest

from evals.model_wrapper import RecordingModel, ScriptedModel, ScriptExhausted, is_guardrail_rejection


def run(coro):
    return asyncio.run(coro)


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
