"""Tests sin red de provision_keys.py (change litellm-key-budget-configurable).

Cubre la lectura del techo de gasto por entorno y la invariante del upsert de no
sobrescribir un budget ya puesto. No toca el proxy ni la red.

    python infra/litellm/test_provision_keys.py
    # o, desde infra/litellm/:  python -m unittest test_provision_keys
"""

import os
import sys
import unittest
from pathlib import Path

# El directorio no es un paquete (sin __init__.py), asi que se importa el script
# por su ruta, como hacen los demas scripts de infra/litellm.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import provision_keys as pk  # noqa: E402


class ReadMaxBudgetTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = os.environ.get(pk._MAX_BUDGET_ENV_VAR)
        os.environ.pop(pk._MAX_BUDGET_ENV_VAR, None)

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop(pk._MAX_BUDGET_ENV_VAR, None)
        else:
            os.environ[pk._MAX_BUDGET_ENV_VAR] = self._saved

    def test_sin_variable_usa_el_defecto(self) -> None:
        self.assertEqual(pk._read_max_budget(), 5.0)

    def test_variable_vacia_usa_el_defecto(self) -> None:
        os.environ[pk._MAX_BUDGET_ENV_VAR] = "   "
        self.assertEqual(pk._read_max_budget(), 5.0)

    def test_valor_de_produccion(self) -> None:
        os.environ[pk._MAX_BUDGET_ENV_VAR] = "50"
        self.assertEqual(pk._read_max_budget(), 50.0)

    def test_valor_no_numerico_falla(self) -> None:
        for bad in ("cincuenta", "50 USD", "5,5"):
            os.environ[pk._MAX_BUDGET_ENV_VAR] = bad
            with self.assertRaises(ValueError):
                pk._read_max_budget()

    def test_valor_no_positivo_falla(self) -> None:
        for bad in ("0", "-5", "-0.01"):
            os.environ[pk._MAX_BUDGET_ENV_VAR] = bad
            with self.assertRaises(ValueError):
                pk._read_max_budget()


class MissingFieldsTest(unittest.TestCase):
    _MODELS = ["generator", "generator-fallback-hf"]

    def test_key_sin_budget_recibe_el_valor_pasado(self) -> None:
        existing = {"max_budget": None, "rpm_limit": 60, "models": self._MODELS}
        missing = pk._missing_fields(existing, self._MODELS, max_budget=50.0)
        self.assertEqual(missing["max_budget"], 50.0)
        self.assertEqual(missing["budget_duration"], pk._BUDGET_DURATION)

    def test_key_con_budget_no_se_sobrescribe(self) -> None:
        # Una key con 5 USD en un proxy donde ahora se aprovisiona con 50: el
        # upsert no debe incluir max_budget (no se pisa un budget ya puesto).
        existing = {"max_budget": 5.0, "rpm_limit": 60, "models": self._MODELS}
        missing = pk._missing_fields(existing, self._MODELS, max_budget=50.0)
        self.assertNotIn("max_budget", missing)
        self.assertNotIn("budget_duration", missing)

    def test_key_completa_no_tiene_campos_que_faltan(self) -> None:
        existing = {"max_budget": 5.0, "rpm_limit": 60, "models": self._MODELS}
        self.assertEqual(pk._missing_fields(existing, self._MODELS, 5.0), {})


if __name__ == "__main__":
    unittest.main()
