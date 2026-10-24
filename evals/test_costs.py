"""Tests del calculador de costes y de la tabla de precios, con valores calculados a mano.

Uso (desde la raiz del repo): python -m unittest evals.test_costs
"""

import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from evals import costs, prices as price_table

PRICES = {
    "currency": "USD",
    "fetched": "2026-10-24",
    "models": {"prod": {"input_per_m": 1.0, "output_per_m": 2.0}, "ref": {"input_per_m": 10.0, "output_per_m": 20.0}},
    "roles": {
        "production": {a: "prod" for a in price_table.AGENTS},
        "reference": {a: "ref" for a in price_table.AGENTS},
    },
    "fallback": {
        "models": {"fb": {"providers": {
            "barato": {"input_per_m": 0.5, "output_per_m": 1.0},
            "caro": {"input_per_m": 3.0, "output_per_m": 6.0}}}},
        "roles": {a: "fb" for a in price_table.AGENTS},
    },
    "tavily": {
        "selected_plan": "project",
        "credits_per_search": 1,
        "plans": {
            "researcher": {"monthly_fee": 0, "included_credits": 1000, "extra_credit_price": None},
            "project": {"monthly_fee": 30, "included_credits": 4000, "extra_credit_price": 0.008},
            "payg": {"monthly_fee": 0, "included_credits": 0, "extra_credit_price": 0.008},
        },
    },
}


def assumptions(**overrides):
    base = {
        "teams_piloto": 1, "teams_equipo": 5, "teams_organizacion": 30, "juniors_per_team": 2,
        "saved_exercises": 500, "candidates_per_generation": 5, "save_rate": 0.9, "exercises_per_junior": 500,
        "new_juniors_per_year": 2, "new_exercises_per_year": 50, "with_repo_share": 0.8,
        "repositories_per_project": 5, "technologies_per_project": 15, "key_multipliers": [1, 2, 4],
        "key_budget_usd_30d": 5.0, "regime_memory_hit": False, "fallback_shares": [0, 0.05, 0.2, 1.0],
    }
    base.update(overrides)
    return {k: {"value": v, "origin": "test", "note": ""} for k, v in base.items()}


def usage(input_tokens, output_tokens, cost, prompt_cost=None, completion_cost=None, complete=True):
    return {"calls": 1, "input_tokens": input_tokens, "output_tokens": output_tokens, "reasoning_tokens": 0,
            "cost": cost, "prompt_cost": prompt_cost, "completion_cost": completion_cost, "cost_complete": complete}


def record(case_id, set_name, agent, u, probe=None, result=None):
    return {"id": case_id, "set": set_name, "agent": agent, "outcome": "ok", "calls": 1, "usage": u,
            "probe": probe, "result": result or {"memory_hit": False}}


def cases():
    return {
        "evaluator": [record("e1", "evaluation", "evaluator", usage(1000, 200, 0.002))],
        "reviewer": [record("e1", "evaluation", "reviewer", usage(500, 100, None, complete=False))],
        "validator": [record("v1", "validation", "validator", usage(400, 50, 0.0005))],
        "web": [record("w1", "web", "web", usage(2000, 300, 0.004), probe={"search_calls": 4})],
        "code": [record("c1", "code", "code", usage(8000, 500, 0.02), probe={"reads": 10})],
        "exercises": [record("g1", "generation", "exercises", usage(3000, 600, 0.0024, 0.0006, 0.0018))],
    }


DATASETS = {"generation": [{"id": "g1", "count": 3}], "evaluation": [], "validation": [], "web": [], "code": [],
            "adversarial": []}


class MeasureAndOperationTests(unittest.TestCase):
    def setUp(self):
        self.measures = costs.measure_agents(cases(), DATASETS)

    def test_media_por_agente(self):
        self.assertEqual(self.measures["evaluator"]["input_tokens"], 1000)
        self.assertAlmostEqual(self.measures["evaluator"]["billed_cost"], 0.002)
        self.assertEqual(self.measures["web"]["searches"], 4)
        self.assertEqual(self.measures["code"]["reads"], 10)

    def test_ejercicios_se_mide_por_candidato(self):
        m = self.measures["exercises"]
        self.assertEqual(m["output_tokens_per_candidate"], 200)       # 600 tokens / 3 candidatos
        self.assertAlmostEqual(m["completion_cost_per_candidate"], 0.0006)

    def test_los_adversariales_y_la_memoria_no_entran_en_la_media(self):
        data = cases()
        data["evaluator"].append(record("a1", "adversarial", "evaluator", usage(9000, 900, 0.9)))
        data["web"].append(record("w2", "web", "web", usage(9999, 999, 9.9), probe={"search_calls": 0},
                                  result={"memory_hit": True}))
        m = costs.measure_agents(data, DATASETS)
        self.assertAlmostEqual(m["evaluator"]["billed_cost"], 0.002)
        self.assertAlmostEqual(m["web"]["billed_cost"], 0.004)

    def test_coste_facturado_y_de_lista(self):
        ops = costs.operations(self.measures, PRICES)
        # El revisor no informo coste: (500 x 1 + 100 x 2) / 1e6 = 0,0007 al precio de lista.
        self.assertAlmostEqual(ops["evaluate_answer"]["cost"], 0.002 + 0.0007)
        self.assertEqual(ops["validate_technology"]["cost"], 0.0005)

    def test_ejercicios_con_cinco_candidatos(self):
        cost = costs.agent_cost(self.measures["exercises"], "exercises", PRICES, "measured", 5)
        self.assertAlmostEqual(cost["cost"], 0.0006 + 5 * 0.0006)     # entrada + 5 candidatos de salida

    def test_composicion_y_desglose_de_generar(self):
        ops = costs.operations(self.measures, PRICES)
        without = ops["generate_without_repo"]
        # validador 0,0005 + web 0,004 + ejercicios 0,0036 + 4 busquedas x 0,008
        self.assertAlmostEqual(without["cost"], 0.0005 + 0.004 + 0.0036 + 0.032)
        self.assertAlmostEqual(without["share"]["tavily_marginal"], 0.032 / without["cost"])
        self.assertAlmostEqual(ops["generate_with_repo"]["cost"], without["cost"] + 0.02)
        self.assertAlmostEqual(ops["generate_memory_hit"]["cost"], 0.0005 + 0.0036)

    def test_agente_sin_datos_no_es_calculable(self):
        data = cases()
        del data["code"]
        ops = costs.operations(costs.measure_agents(data, DATASETS), PRICES)
        self.assertIsNone(ops["generate_with_repo"]["cost"])
        self.assertEqual(ops["generate_with_repo"]["missing"], ["code"])
        self.assertIsNotNone(ops["generate_without_repo"]["cost"])

    def test_referencia_con_los_mismos_tokens(self):
        ref = costs.agent_cost(self.measures["evaluator"], "evaluator", PRICES, "reference")
        self.assertAlmostEqual(ref["cost"], (1000 * 10 + 200 * 20) / 1e6)


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.measures = costs.measure_agents(cases(), DATASETS)

    def run_campaign(self, teams=1, **overrides):
        return costs.campaign("piloto", teams, self.measures, assumptions(**overrides), PRICES)

    def test_generaciones_a_partir_de_ejercicios_guardados(self):
        self.assertEqual(costs.generations_needed(500, 5, 0.9), 112)      # 500 / 4,5 = 111,1
        self.assertEqual(costs.generations_needed(500, 3, 0.9), 186)

    def test_fallos_de_memoria_acotados_por_claves(self):
        self.assertEqual(costs.memory_misses(112, 15), 15)
        self.assertEqual(costs.memory_misses(90, 75), 75)
        self.assertEqual(costs.memory_misses(10, 15), 10)                   # menos generaciones que claves

    def test_fases_de_un_equipo(self):
        c = self.run_campaign()
        self.assertEqual(c["generations_per_tech_lead"], 112)
        self.assertEqual(c["generations_with_repo"], 90)
        self.assertEqual((c["memory"]["web_misses"], c["memory"]["code_misses"]), (15, 75))
        # validador 112 x 0,0005 + ejercicios 112 x 0,0036 + web 15 x 0,004 + codigo 75 x 0,02
        self.assertAlmostEqual(c["phases_per_team"]["generation"], 0.056 + 0.4032 + 0.06 + 1.5)
        self.assertEqual(c["evaluations_per_team"], 1000)
        self.assertAlmostEqual(c["phases_per_team"]["resolution"], 1000 * 0.002 + 1000 * 0.0007)
        regime = 12 * (0.0005 + 0.0036) + 12 * 0.004 + 10 * 0.02 + (2 * 500 + 2 * 50) * 0.0027
        self.assertAlmostEqual(c["phases_per_team"]["regime_year"], regime)

    def test_reparto_entre_generacion_y_evaluacion(self):
        c = self.run_campaign()
        self.assertAlmostEqual(c["share"]["generation"] + c["share"]["evaluation"], 1.0)
        self.assertAlmostEqual(c["share"]["evaluation"], 2.7 / (2.0192 + 2.7))

    def test_costes_unitarios_sin_ahorros(self):
        u = self.run_campaign()["unit_costs"]
        self.assertAlmostEqual(u["per_saved_exercise"], 2.0192 / 500)
        self.assertAlmostEqual(u["per_evaluation"], 0.0027)
        self.assertAlmostEqual(u["per_junior_trained"], 500 * 0.0027 + 2.0192 / 2)
        self.assertNotIn("saving", json.dumps(self.run_campaign()).lower())

    def test_presupuesto_de_clave_superado(self):
        self.assertEqual(self.run_campaign()["keys_over_budget"], [])
        over = self.run_campaign(key_budget_usd_30d=1.0)
        self.assertEqual(over["keys_over_budget"], ["code", "evaluator"])

    def test_el_pico_suma_todos_los_equipos(self):
        c = self.run_campaign(teams=30)
        self.assertAlmostEqual(c["peak_30d_per_key"]["evaluator"], 30 * 2.0)
        self.assertIn("evaluator", c["keys_over_budget"])

    def test_tavily_dentro_del_plan_por_encima_e_insuficiente(self):
        one = self.run_campaign()["tavily"]["campaign"]
        self.assertEqual(one["project"]["credits"], 60)                    # 15 fallos x 4 busquedas
        self.assertEqual(one["project"]["cost"], 30)
        self.assertEqual(one["researcher"]["cost"], 0)
        org = self.run_campaign(teams=30)["tavily"]["campaign"]
        self.assertEqual(org["project"]["credits"], 1800)
        self.assertFalse(org["researcher"]["sufficient"])                 # 1.800 > 1.000 y sin exceso
        self.assertIsNone(org["researcher"]["cost"])
        big = costs._tavily_cost(PRICES, 4500, 1, "project")
        self.assertAlmostEqual(big["cost"], 30 + 500 * 0.008)

    def test_sensibilidad_al_numero_de_claves(self):
        s = self.run_campaign()["sensitivity"]
        self.assertEqual((s["1"]["web_misses"], s["1"]["code_misses"]), (15, 75))
        self.assertEqual((s["2"]["web_misses"], s["2"]["code_misses"]), (30, 90))     # el codigo se acota por sus 90 generaciones
        self.assertGreater(s["4"]["generation_cost_per_team"], s["1"]["generation_cost_per_team"])

    def test_agente_sin_datos_no_calcula_la_campana(self):
        data = cases()
        del data["code"]
        c = costs.campaign("piloto", 1, costs.measure_agents(data, DATASETS), assumptions(), PRICES)
        self.assertFalse(c["computable"])
        self.assertEqual(c["missing"], ["code"])


class FallbackTests(unittest.TestCase):
    def setUp(self):
        self.measures = costs.measure_agents(cases(), DATASETS)

    def test_rango_por_proveedor(self):
        low = price_table.fallback_price(PRICES, "evaluator", "min")
        high = price_table.fallback_price(PRICES, "evaluator", "max")
        self.assertEqual((low["provider"], high["provider"]), ("barato", "caro"))

    def test_mismos_tokens_con_el_precio_del_respaldo(self):
        low = costs.agent_cost(self.measures["evaluator"], "evaluator", PRICES, "fallback_min")
        high = costs.agent_cost(self.measures["evaluator"], "evaluator", PRICES, "fallback_max")
        self.assertAlmostEqual(low["cost"], (1000 * 0.5 + 200 * 1.0) / 1e6)       # 0,0007
        self.assertAlmostEqual(high["cost"], (1000 * 3.0 + 200 * 6.0) / 1e6)      # 0,0042

    def test_operacion_con_respaldo(self):
        ops = costs.operations(self.measures, PRICES, "fallback_min")
        # evaluador 0,0007 + revisor (500 x 0,5 + 100 x 1,0) / 1e6 = 0,00035
        self.assertAlmostEqual(ops["evaluate_answer"]["cost"], 0.0007 + 0.00035)

    def test_fraccion_cero_es_el_medido_y_cien_es_el_respaldo(self):
        report = costs.build_cost_report(cases(), DATASETS, PRICES, assumptions())
        measured = report["campaign"]["piloto"]["campaign_llm_cost"]
        weighted = report["fallback"]["weighted"]["piloto"]
        low = report["fallback"]["campaign"]["piloto"]["min"]["campaign_llm_cost"]
        high = report["fallback"]["campaign"]["piloto"]["max"]["campaign_llm_cost"]
        self.assertAlmostEqual(weighted["0"]["min"], measured)
        self.assertAlmostEqual(weighted["0"]["max"], measured)
        self.assertAlmostEqual(weighted["1.0"]["min"], low)
        self.assertAlmostEqual(weighted["1.0"]["max"], high)
        self.assertAlmostEqual(weighted["0.2"]["max"], 0.8 * measured + 0.2 * high)

    def test_el_markdown_declara_que_la_fraccion_no_se_mide(self):
        text = costs.render_markdown(costs.build_cost_report(cases(), DATASETS, PRICES, assumptions()))
        self.assertIn("Sensibilidad al modelo de respaldo", text)
        self.assertIn("no se mide", text)
        self.assertIn("20% al respaldo", text)

    def test_sin_todas_las_mediciones_la_campana_con_respaldo_no_es_calculable(self):
        data = cases()
        del data["code"]
        report = costs.build_cost_report(data, DATASETS, PRICES, assumptions())
        self.assertEqual(report["fallback"]["weighted"], {})
        self.assertIn("Campana con respaldo: no calculable", costs.render_markdown(report))

    def test_respaldo_sin_precio_falla(self):
        prices = copy.deepcopy(PRICES)
        prices["fallback"]["models"]["fb"]["providers"] = {}
        with self.assertRaisesRegex(price_table.PriceError, "no tiene precios"):
            price_table.fallback_price(prices, "evaluator", "min")


class ReportTests(unittest.TestCase):
    def build(self):
        return costs.build_cost_report(cases(), DATASETS, PRICES, assumptions())

    def test_determinista(self):
        self.assertEqual(json.dumps(self.build(), sort_keys=True), json.dumps(self.build(), sort_keys=True))

    def test_comparativa_con_la_referencia(self):
        comparison = self.build()["reference_comparison"]["piloto"]
        self.assertGreater(comparison["reference"], comparison["measured"])
        self.assertAlmostEqual(comparison["factor"], comparison["reference"] / comparison["measured"])

    def test_comprobacion_cruzada_facturado_frente_a_lista(self):
        check = self.build()["crosscheck"]["evaluator"]
        self.assertAlmostEqual(check["billed"], 0.002)
        self.assertAlmostEqual(check["list_price"], (1000 * 1 + 200 * 2) / 1e6)
        self.assertAlmostEqual(check["ratio"], 0.002 / 0.0014)

    def test_el_markdown_lista_los_supuestos_y_no_habla_de_ahorro(self):
        text = costs.render_markdown(self.build())
        self.assertIn("## Supuestos", text)
        self.assertIn("saved_exercises", text)
        self.assertNotIn("ahorro", text.lower())
        self.assertIn("Campana - nivel piloto", text)

    def test_markdown_con_agente_sin_datos(self):
        data = cases()
        del data["web"]
        text = costs.render_markdown(costs.build_cost_report(data, DATASETS, PRICES, assumptions()))
        self.assertIn("Faltan mediciones de:** web", text)
        self.assertIn("no calculable", text)

    def test_rechaza_informes_simulados(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "informe.json"
            path.write_text(json.dumps({"mode": "simulated", "cases": cases()}), encoding="utf-8")
            with self.assertRaisesRegex(costs.CostError, "modo real"):
                costs.merge_reports([path])

    def test_el_ultimo_informe_manda_por_agente(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "a.json", Path(tmp) / "b.json"
            old = cases()
            new = {"evaluator": [record("e9", "evaluation", "evaluator", usage(1, 1, 0.5))]}
            first.write_text(json.dumps({"mode": "real", "cases": old}), encoding="utf-8")
            second.write_text(json.dumps({"mode": "real", "cases": new}), encoding="utf-8")
            merged = costs.merge_reports([first, second])["cases"]
            self.assertEqual(merged["evaluator"][0]["id"], "e9")
            self.assertEqual(merged["web"][0]["id"], "w1")


class PricesTests(unittest.TestCase):
    RESPONSE = {"data": [
        {"id": "a/b", "pricing": {"prompt": "0.00000002", "completion": "0.000001"}},
        {"id": "c/d", "pricing": {"prompt": "", "completion": "0.000001"}},
    ]}

    def test_extrae_precio_por_millon(self):
        found = price_table.extract_prices(self.RESPONSE, ["a/b", "c/d", "no/existe"])
        self.assertEqual(found, {"a/b": {"input_per_m": 0.02, "output_per_m": 1.0}})

    def test_modelo_ausente_falla_en_lugar_de_suponer_un_precio(self):
        with self.assertRaisesRegex(price_table.PriceError, "no esta en la tabla"):
            price_table.model_price(PRICES, "otro/modelo")

    def test_modelo_sin_precio_falla(self):
        prices = copy.deepcopy(PRICES)
        prices["models"]["prod"]["input_per_m"] = None
        with self.assertRaisesRegex(price_table.PriceError, "sin precio"):
            price_table.model_price(prices, "prod")

    def test_coste_por_tokens(self):
        self.assertAlmostEqual(price_table.token_cost(PRICES, "prod", 1_000_000, 500_000), 1.0 + 1.0)

    def test_refresco_actualiza_precio_y_fecha_sin_credenciales(self):
        table = copy.deepcopy(PRICES)
        table["models"] = {"a/b": {"input_per_m": 9.0, "output_per_m": 9.0}}
        table["roles"] = {"production": {a: "a/b" for a in price_table.AGENTS},
                          "reference": {a: "a/b" for a in price_table.AGENTS}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prices.json"
            path.write_text(json.dumps(table), encoding="utf-8")
            changes = price_table.refresh(path, models_response=self.RESPONSE, today=date(2026, 11, 1))
            saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["fetched"], "2026-11-01")
        self.assertEqual(saved["models"]["a/b"], {"input_per_m": 0.02, "output_per_m": 1.0})
        self.assertIn("a/b", changes)

    HF_RESPONSE = {"data": [{"id": "x/y", "providers": [
        {"provider": "uno", "status": "live", "pricing": {"input": 0.2, "output": 0.6}},
        {"provider": "dos", "status": "live", "pricing": None},
        {"provider": "tres", "status": "offline", "pricing": {"input": 9, "output": 9}},
    ]}]}

    def test_precios_del_respaldo_solo_de_proveedores_activos_con_precio(self):
        found = price_table.extract_hf_prices(self.HF_RESPONSE, ["x/y", "no/existe"])
        self.assertEqual(found, {"x/y": {"uno": {"input_per_m": 0.2, "output_per_m": 0.6}}})

    def test_refresco_actualiza_tambien_el_respaldo(self):
        table = copy.deepcopy(PRICES)
        table["fallback"] = {"source": "x", "fetched": None, "models": {"x/y": {"providers": {}}},
                             "roles": {a: "x/y" for a in price_table.AGENTS}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prices.json"
            path.write_text(json.dumps(table), encoding="utf-8")
            changes = price_table.refresh(path, models_response={"data": []}, today=date(2026, 11, 1),
                                          hf_response=self.HF_RESPONSE)
            saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("hf:x/y", changes)
        self.assertEqual(saved["fallback"]["models"]["x/y"]["providers"]["uno"]["input_per_m"], 0.2)
        self.assertEqual(saved["fallback"]["fetched"], "2026-11-01")

    def test_plan_de_tavily(self):
        plan = price_table.tavily_plan(PRICES)
        self.assertEqual((plan["name"], plan["monthly_fee"], plan["included_credits"]), ("project", 30, 4000))
        with self.assertRaises(price_table.PriceError):
            price_table.tavily_plan(PRICES, "inexistente")

    def test_el_fichero_del_repositorio_es_valido(self):
        real = price_table.load_prices()
        for kind in ("production", "reference"):
            for agent in price_table.AGENTS:
                price_table.model_price(real, real["roles"][kind][agent])     # todos con precio
        for agent in price_table.AGENTS:
            low = price_table.fallback_price(real, agent, "min")
            high = price_table.fallback_price(real, agent, "max")
            self.assertLessEqual(low["input_per_m"] + low["output_per_m"], high["input_per_m"] + high["output_per_m"])


class RepositoryFilesTests(unittest.TestCase):
    def test_los_supuestos_del_repositorio_cargan_y_declaran_su_origen(self):
        loaded = costs.load_assumptions()
        self.assertEqual(costs.value(loaded, "saved_exercises"), 500)
        for name, entry in loaded.items():
            self.assertIn(entry["origin"], ("usuario", "capstone", "hipotesis"), name)


if __name__ == "__main__":
    unittest.main()
