"""Tests de las metricas puras, con valores calculados a mano.

Uso (desde la raiz del repo): python -m unittest evals.test_metrics
"""

import unittest

from evals import metrics


class RateTests(unittest.TestCase):
    def test_sin_casos_no_es_cero(self):
        self.assertIsNone(metrics.rate(0, 0))

    def test_proporcion(self):
        self.assertEqual(metrics.rate(1, 4), 0.25)


class AccuracyAndKappaTests(unittest.TestCase):
    def test_coincidencia_total(self):
        pairs = [("correct", "correct"), ("incorrect", "incorrect"), ("incomplete", "incomplete")]
        self.assertEqual(metrics.accuracy(pairs), 1.0)
        self.assertEqual(metrics.cohen_kappa(pairs), 1.0)

    def test_kappa_calculado_a_mano(self):
        # 10 casos: 4 correct (3 bien, 1 como incomplete), 3 incomplete (2 bien,
        # 1 como incorrect), 3 incorrect (todos bien).
        pairs = (
            [("correct", "correct")] * 3
            + [("correct", "incomplete")]
            + [("incomplete", "incomplete")] * 2
            + [("incomplete", "incorrect")]
            + [("incorrect", "incorrect")] * 3
        )
        # observado = 8/10. Marginales esperados: correct .4, incomplete .3, incorrect .3.
        # Marginales obtenidos: correct .3, incomplete .3, incorrect .4.
        # azar = .4*.3 + .3*.3 + .3*.4 = .12 + .09 + .12 = .33
        # kappa = (.8 - .33) / (1 - .33) = .47 / .67
        self.assertAlmostEqual(metrics.accuracy(pairs), 0.8)
        self.assertAlmostEqual(metrics.cohen_kappa(pairs), 0.47 / 0.67)

    def test_kappa_sin_casos(self):
        self.assertIsNone(metrics.cohen_kappa([]))

    def test_kappa_una_sola_etiqueta(self):
        self.assertEqual(metrics.cohen_kappa([("correct", "correct")] * 3), 1.0)
        # Todo "correct" esperado y todo "incorrect" obtenido: sin acuerdo alguno.
        self.assertEqual(metrics.cohen_kappa([("correct", "incorrect")] * 3), 0.0)

    def test_matriz_de_confusion(self):
        pairs = [("correct", "correct"), ("correct", "incorrect"), ("incorrect", "incorrect")]
        matrix = metrics.confusion_matrix(pairs)
        self.assertEqual(matrix["correct"], {"correct": 1, "incomplete": 0, "incorrect": 1})
        self.assertEqual(matrix["incomplete"], {"correct": 0, "incomplete": 0, "incorrect": 0})
        self.assertEqual(matrix["incorrect"]["incorrect"], 1)


class PercentileTests(unittest.TestCase):
    def test_rango_mas_cercano(self):
        values = list(range(1, 11))  # 1..10
        self.assertEqual(metrics.percentile(values, 50), 5)
        self.assertEqual(metrics.percentile(values, 95), 10)
        self.assertEqual(metrics.percentile(values, 99), 10)

    def test_un_solo_valor(self):
        self.assertEqual(metrics.percentile([7.0], 50), 7.0)

    def test_sin_valores(self):
        self.assertIsNone(metrics.percentile([], 95))
        self.assertEqual(
            metrics.latency_summary([]), {"p50_ms": None, "p95_ms": None, "p99_ms": None}
        )


class OverlapTests(unittest.TestCase):
    def test_enunciado_repetido_es_maximo(self):
        text = "Que hace el decorador post en FastAPI sobre una ruta"
        self.assertEqual(metrics.max_overlap([text], [text]), 1.0)

    def test_enunciados_distintos_solapan_poco(self):
        value = metrics.max_overlap(
            ["Para que sirve el hook useState en React"],
            ["Como declara FastAPI un parametro de consulta opcional"],
        )
        self.assertLess(value, 0.2)

    def test_sin_previos(self):
        self.assertIsNone(metrics.max_overlap(["algo"], []))

    def test_jaccard_a_mano(self):
        a = frozenset({"react", "hook", "estado"})
        b = frozenset({"react", "hook", "efecto"})
        self.assertAlmostEqual(metrics.jaccard(a, b), 2 / 4)

    def test_terminos_ignoran_tildes_y_vacias(self):
        self.assertEqual(metrics.terms("¿Qué hace el Decorador?"), frozenset({"decorador"}))


class PrecisionRecallTests(unittest.TestCase):
    def test_a_mano(self):
        precision, recall = metrics.precision_recall({"a", "b", "c"}, {"a", "b", "d", "e"})
        self.assertAlmostEqual(precision, 2 / 3)
        self.assertAlmostEqual(recall, 2 / 4)

    def test_sin_predicciones(self):
        self.assertEqual(metrics.precision_recall(set(), {"a"}), (None, 0.0))

    def test_sin_esperados(self):
        self.assertEqual(metrics.precision_recall({"a"}, set()), (0.0, None))


if __name__ == "__main__":
    unittest.main()
