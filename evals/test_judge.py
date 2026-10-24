"""Tests del juez de contenido (`evals/judge.py`), sin red ni modelos."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from evals import judge, judge_dataset

GOOD = json.dumps({
    "scores": {"unicidad_de_concepto": 2, "autosuficiencia": 1, "nivel": 2,
               "calidad_del_fallo": None, "utilidad_de_la_justificacion": 1},
    "justification": "Enunciado de un solo concepto y nivel adecuado; algo impreciso en la respuesta.",
})


def _case(case_id="jg-1", exercise_type="knowledge"):
    return {"id": case_id, "type": exercise_type, "statement": "¿Qué hace `list.append`?",
            "code": [], "expected_answer": "Añade un elemento al final."}


class ParseTests(unittest.TestCase):
    def test_valido(self):
        parsed = judge._parse(GOOD, "knowledge")
        self.assertEqual(parsed["scores"]["nivel"], 2)
        self.assertIsNone(parsed["scores"]["calidad_del_fallo"])

    def test_json_invalido(self):
        self.assertIsNone(judge._parse("Claro, el ejercicio está bien.", "knowledge"))

    def test_falta_criterio(self):
        bad = json.dumps({"scores": {"unicidad_de_concepto": 2}, "justification": "x"})
        self.assertIsNone(judge._parse(bad, "knowledge"))

    def test_conocimiento_exige_null_en_fallo(self):
        bad = json.dumps({"scores": {"unicidad_de_concepto": 2, "autosuficiencia": 2, "nivel": 2,
                                     "calidad_del_fallo": 1, "utilidad_de_la_justificacion": 2},
                          "justification": "x"})
        self.assertIsNone(judge._parse(bad, "knowledge"))

    def test_justificacion_vacia(self):
        bad = json.dumps({"scores": {"unicidad_de_concepto": 2, "autosuficiencia": 2, "nivel": 2,
                                     "calidad_del_fallo": None, "utilidad_de_la_justificacion": 2},
                          "justification": "   "})
        self.assertIsNone(judge._parse(bad, "knowledge"))


class JudgeCaseTests(unittest.TestCase):
    def test_salida_valida_a_la_primera(self):
        calls = []

        def invoke(system, user):
            calls.append(user)
            return GOOD

        record = judge.judge_case(_case(), invoke)
        self.assertEqual(record["outcome"], "ok")
        self.assertEqual(record["calls"], 1)

    def test_reintenta_una_vez_y_luego_ok(self):
        script = ["no es json", GOOD]

        def invoke(system, user):
            return script.pop(0)

        record = judge.judge_case(_case(), invoke)
        self.assertEqual(record["outcome"], "ok")
        self.assertEqual(record["calls"], 2)

    def test_dos_salidas_malas_no_juzgado(self):
        record = judge.judge_case(_case(), lambda system, user: "sigue sin ser json")
        self.assertEqual(record["outcome"], "not_judged")
        self.assertEqual(record["calls"], 2)
        self.assertIsNone(record["scores"])


class CalibrationTests(unittest.TestCase):
    def _cases_with(self, judge_scores):
        return [{"id": f"c{i}", "scores": {"unicidad_de_concepto": s, "autosuficiencia": s, "nivel": s,
                                           "calidad_del_fallo": None, "utilidad_de_la_justificacion": s}}
                for i, s in enumerate(judge_scores)]

    def test_kappa_perfecto(self):
        cases = self._cases_with([0, 1, 2])
        human = {f"c{i}": {"unicidad_de_concepto": s, "autosuficiencia": s, "nivel": s,
                           "calidad_del_fallo": None, "utilidad_de_la_justificacion": s}
                 for i, s in enumerate([0, 1, 2])}
        result = judge.calibration(cases, human)
        self.assertEqual(result["criteria"]["nivel"]["pairs"], 3)
        self.assertAlmostEqual(result["criteria"]["nivel"]["kappa"], 1.0)

    def test_kappa_desacuerdo(self):
        cases = self._cases_with([2, 1, 0])
        human = {f"c{i}": {"nivel": s} for i, s in enumerate([0, 1, 2])}
        result = judge.calibration(cases, human)
        self.assertAlmostEqual(result["criteria"]["nivel"]["kappa"], 0.0)

    def test_sin_humanas(self):
        self.assertIsNone(judge.calibration(self._cases_with([1]), {}))


class DatasetTests(unittest.TestCase):
    def test_conjunto_del_repositorio_carga(self):
        cases = judge_dataset.load()
        self.assertGreaterEqual(len(cases), 4)
        self.assertTrue(any(c["type"] == "debug" for c in cases))

    def test_caso_mal_formado(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "judge.jsonl"
            path.write_text('{"id": "x", "type": "quiz", "statement": "s", "code": [], "expected_answer": "e"}\n',
                            encoding="utf-8")
            with self.assertRaises(judge_dataset.JudgeDatasetError) as ctx:
                judge_dataset.load(path)
            self.assertIn("type", str(ctx.exception))

    def test_humanas_separadas(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "human.json"
            path.write_text(json.dumps({"_comment": "x", "c1": {"nivel": 2}}), encoding="utf-8")
            human = judge_dataset.load_human(path)
            self.assertEqual(human, {"c1": {"nivel": 2}})


class ReportTests(unittest.TestCase):
    def test_informe_con_medias_y_sin_calibracion(self):
        record = {"id": "c1", "type": "knowledge", "outcome": "ok", "error": None,
                  "scores": {"unicidad_de_concepto": 2, "autosuficiencia": 2, "nivel": 1,
                             "calidad_del_fallo": None, "utilidad_de_la_justificacion": 2},
                  "justification": "x", "calls": 1}
        report = judge.build_report([record], {}, "modelo/juez", now=datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(report["means"]["nivel"], 1)
        self.assertIsNone(report["means"]["calidad_del_fallo"])
        self.assertIsNone(report["calibration"])
        self.assertIn("calibracion: n/d", judge.render_summary(report))


if __name__ == "__main__":
    unittest.main()