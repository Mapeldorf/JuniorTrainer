"""Tests de la carga y validacion del dataset.

Uso (desde la raiz del repo): python -m unittest evals.test_dataset
"""

import json
import tempfile
import unittest
from pathlib import Path

from evals import dataset

_EVAL_CASE = {
    "id": "ev-x",
    "statement": "Que hace X",
    "code": [],
    "expected_answer": None,
    "student_answer": "respuesta",
    "label": "correct",
    "proposed_justification": "bien",
}
_VAL_CASE = {
    "id": "va-x",
    "technologies": ["React"],
    "context": "generation",
    "catalog": [],
    "expect_valid": True,
}
_GEN_CASE = {
    "id": "ge-x",
    "type": "knowledge",
    "count": 2,
    "technologies": ["React"],
    "web_result": None,
    "code_result": None,
    "saved_statements": [],
    "topics": ["a", "b"],
}
_ADV_CASE = {**_EVAL_CASE, "id": "ad-x", "target": "evaluator", "kind": "inyeccion"}


def _write(directory: Path, name: str, cases: list[dict]) -> None:
    (directory / f"{name}.jsonl").write_text(
        "\n".join(json.dumps(c) for c in cases), encoding="utf-8"
    )


def _write_all(directory: Path, **overrides) -> None:
    labels = [
        {**_EVAL_CASE, "id": f"ev-{label}", "label": label}
        for label in ("correct", "incomplete", "incorrect")
    ]
    sets = {
        "evaluation": labels,
        "validation": [_VAL_CASE],
        "generation": [_GEN_CASE],
        "adversarial": [_ADV_CASE],
    }
    sets.update(overrides)
    for name, cases in sets.items():
        _write(directory, name, cases)


class LoadTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_dataset_valido(self):
        _write_all(self.dir)
        data = dataset.load_all(self.dir)
        self.assertEqual(set(data), set(dataset.SET_NAMES))

    def test_conjunto_vacio(self):
        _write_all(self.dir, validation=[])
        with self.assertRaisesRegex(dataset.DatasetError, "validation: el conjunto no tiene ningun caso"):
            dataset.load_all(self.dir)

    def test_conjunto_ausente(self):
        _write_all(self.dir)
        (self.dir / "adversarial.jsonl").unlink()
        with self.assertRaisesRegex(dataset.DatasetError, "adversarial: no existe"):
            dataset.load_all(self.dir)

    def test_id_duplicado(self):
        _write_all(self.dir, validation=[_VAL_CASE, _VAL_CASE])
        with self.assertRaisesRegex(dataset.DatasetError, r"validation/va-x: campo 'id': identificador duplicado"):
            dataset.load_all(self.dir)

    def test_campo_ausente_nombra_conjunto_caso_y_campo(self):
        broken = {k: v for k, v in _VAL_CASE.items() if k != "catalog"}
        _write_all(self.dir, validation=[broken])
        with self.assertRaisesRegex(dataset.DatasetError, r"validation/va-x: campo 'catalog': falta"):
            dataset.load_all(self.dir)

    def test_valor_fuera_de_rango(self):
        _write_all(self.dir, generation=[{**_GEN_CASE, "count": 9}])
        with self.assertRaisesRegex(dataset.DatasetError, r"generation/ge-x: campo 'count'"):
            dataset.load_all(self.dir)

    def test_etiqueta_desconocida(self):
        _write_all(self.dir, evaluation=[{**_EVAL_CASE, "label": "maybe"}])
        with self.assertRaisesRegex(dataset.DatasetError, r"evaluation/ev-x: campo 'label'"):
            dataset.load_all(self.dir)

    def test_faltan_etiquetas_de_veredicto(self):
        _write_all(self.dir, evaluation=[_EVAL_CASE])
        with self.assertRaisesRegex(dataset.DatasetError, "faltan casos etiquetados"):
            dataset.load_all(self.dir)

    def test_sim_expect_mal_formado(self):
        _write_all(self.dir, validation=[{**_VAL_CASE, "sim_expect": {"outcome": "nope", "calls": 1}}])
        with self.assertRaisesRegex(dataset.DatasetError, r"campo 'sim_expect'"):
            dataset.load_all(self.dir)

    def test_generacion_sin_temas_ni_sim(self):
        broken = {k: v for k, v in _GEN_CASE.items() if k != "topics"}
        _write_all(self.dir, generation=[broken])
        with self.assertRaisesRegex(dataset.DatasetError, r"campo 'topics'"):
            dataset.load_all(self.dir)


class RepositoryDatasetTests(unittest.TestCase):
    """El dataset versionado en el repositorio tiene que cargar siempre."""

    def test_dataset_del_repositorio_carga(self):
        data = dataset.load_all()
        for name in dataset.SET_NAMES:
            self.assertGreater(len(data[name]), 0, name)


if __name__ == "__main__":
    unittest.main()
