"""Tests del gate de umbrales (`evals/gates.py`), sin red."""

import json
import tempfile
import unittest
from pathlib import Path

from evals import gates


def _report():
    return {"agents": {
        "evaluator": {"executed": True,
                      "metrics": {"valid_output_rate": 1.0,
                                  "verdict": {"accuracy": 0.5, "cohen_kappa": 0.4}},
                      "latency": {"p95_ms": 100000}},
        "validator": {"executed": True,
                      "metrics": {"valid_output_rate": 0.9,
                                  "guardrail_false_positive_rate": {"rate": 0.0}}},
        "notrun": {"executed": False, "reason": "no arranco"},
    }}


THRESHOLDS = [
    {"agent": "evaluator", "metric": "metrics.verdict.accuracy", "min": 0.85},
    {"agent": "evaluator", "metric": "metrics.verdict.cohen_kappa", "min": 0.6},
    {"agent": "evaluator", "metric": "latency.p95_ms", "max": 45000},
    {"agent": "validator", "metric": "metrics.valid_output_rate", "min": 0.98},
    {"agent": "*", "metric": "metrics.guardrail_false_positive_rate.rate", "max": 0.05},
    {"agent": "evaluator", "metric": "metrics.missing_metric", "min": 0.5},
]


class EvaluateTests(unittest.TestCase):
    def test_incumplimientos_y_sin_casos(self):
        gate = gates.evaluate(_report(), THRESHOLDS)
        self.assertEqual(gate["evaluated"], 5)
        incumplidas = {f["metric"] for f in gate["failures"]}
        self.assertEqual(incumplidas, {"metrics.verdict.accuracy", "metrics.verdict.cohen_kappa",
                                       "latency.p95_ms", "metrics.valid_output_rate"})
        sin_casos = {n["metric"] for n in gate["not_evaluated"]}
        self.assertEqual(sin_casos, {"metrics.guardrail_false_positive_rate.rate", "metrics.missing_metric"})
        # el agente no ejecutado no se evalua
        self.assertNotIn("notrun", {f["agent"] for f in gate["failures"]} | {n["agent"] for n in gate["not_evaluated"]})

    def test_todo_dentro(self):
        report = _report()
        report["agents"]["evaluator"]["metrics"]["verdict"] = {"accuracy": 0.9, "cohen_kappa": 0.7}
        report["agents"]["evaluator"]["latency"]["p95_ms"] = 1000
        report["agents"]["validator"]["metrics"]["valid_output_rate"] = 1.0
        report["agents"]["evaluator"]["metrics"]["guardrail_false_positive_rate"] = {"rate": 0.0}
        report["agents"]["evaluator"]["metrics"]["missing_metric"] = 0.9
        gate = gates.evaluate(report, THRESHOLDS)
        self.assertEqual(gate["failures"], [])

    def test_resumen_nombra_la_metrica(self):
        gate = gates.evaluate(_report(), THRESHOLDS)
        text = gates.render_summary(gate)
        self.assertIn("INCUMPLE", text)
        self.assertIn("metrics.verdict.accuracy", text)


class LoadTests(unittest.TestCase):
    def test_tabla_del_repositorio(self):
        self.assertTrue(gates.load())

    def test_no_es_lista(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.json"
            path.write_text(json.dumps({"agent": "x"}), encoding="utf-8")
            with self.assertRaises(gates.GatesError):
                gates.load(path)

    def test_min_y_max_a_la_vez(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.json"
            path.write_text(json.dumps([{"agent": "x", "metric": "y", "min": 0, "max": 1}]), encoding="utf-8")
            with self.assertRaises(gates.GatesError):
                gates.load(path)

    def test_sin_min_ni_max(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.json"
            path.write_text(json.dumps([{"agent": "x", "metric": "y"}]), encoding="utf-8")
            with self.assertRaises(gates.GatesError):
                gates.load(path)


if __name__ == "__main__":
    unittest.main()