"""Calculador de costes (capstone 3.8) a partir de informes de evaluacion REALES.

    python -m evals.costs evals/results/<informe-real>.json [otro-informe.json ...]

Entradas: uno o varios informes del modo real (si un agente aparece en varios,
vale el ultimo), `evals/prices.json` y `evals/cost_assumptions.json`. No llama a
ningun modelo ni a la red, y su salida es determinista: dos ejecuciones con las
mismas entradas dan el mismo informe.

Mide COSTES, no beneficios: no estima ahorros, retornos ni puntos de equilibrio
(decision del usuario: no son calculables). Solo biblioteca estandar.
"""

import argparse
import json
import math
import sys
from pathlib import Path

from evals import dataset, prices as price_table

ASSUMPTIONS_PATH = Path(__file__).resolve().parent / "cost_assumptions.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
AGENTS = price_table.AGENTS
LEVELS = ("piloto", "equipo", "organizacion")

GENERATION_AGENTS = ("validator", "web", "code", "exercises")
EVALUATION_AGENTS = ("evaluator", "reviewer")


class CostError(ValueError):
    """Las entradas no permiten calcular costes (informe simulado, supuesto ausente...)."""


# --------------------------------------------------------------- entradas --

def load_assumptions(path: Path = ASSUMPTIONS_PATH) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))["assumptions"]
    required = ("teams_piloto", "teams_equipo", "teams_organizacion", "juniors_per_team", "saved_exercises",
                "candidates_per_generation", "save_rate", "exercises_per_junior", "new_juniors_per_year",
                "new_exercises_per_year", "with_repo_share", "repositories_per_project",
                "technologies_per_project", "key_multipliers", "key_budget_usd_30d", "key_cap_margin",
                "regime_memory_hit", "fallback_shares")
    missing = [k for k in required if k not in data]
    if missing:
        raise CostError(f"cost_assumptions.json: faltan los supuestos {missing}")
    return data


def value(assumptions: dict, name: str):
    return assumptions[name]["value"]


def merge_reports(paths: list[Path]) -> dict:
    """Une informes reales: por agente vale el de la ultima ruta que lo trae."""
    cases: dict[str, list] = {}
    modes = set()
    for path in paths:
        report = json.loads(Path(path).read_text(encoding="utf-8"))
        modes.add(report.get("mode"))
        for agent, records in report.get("cases", {}).items():
            if records:
                cases[agent] = records
    if "simulated" in modes or None in modes:
        raise CostError("el calculo de costes exige informes del modo real: un informe simulado no trae tokens ni coste")
    return {"cases": cases, "reports": [str(p) for p in paths]}


# --------------------------------------------------------------- medicion --

def _mean(values: list) -> float | None:
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else None


def measure_agents(cases: dict[str, list], datasets: dict[str, list[dict]]) -> dict[str, dict | None]:
    """Tokens y coste medios por llamada completa de cada agente, solo con casos
    de calidad (no adversariales) que llegaron a llamar al modelo."""
    by_id = {c["id"]: c for rows in datasets.values() for c in rows}
    out: dict[str, dict | None] = {}
    for agent in AGENTS:
        records = [r for r in cases.get(agent, []) if r["set"] != "adversarial" and r.get("usage")]
        if agent in ("web", "code"):
            # Con acierto de memoria no hay llamada al modelo: no es una medicion del coste de investigar/analizar.
            records = [r for r in records if r["outcome"] == "ok" and not r["result"]["memory_hit"]]
        if not records:
            out[agent] = None
            continue
        usages = [r["usage"] for r in records]
        measure = {
            "cases": len(records),
            "calls": sum(u["calls"] for u in usages),
            "input_tokens": _mean([u["input_tokens"] for u in usages]),
            "output_tokens": _mean([u["output_tokens"] for u in usages]),
            "reasoning_tokens": _mean([u["reasoning_tokens"] for u in usages]),
            "billed_cost": _mean([u["cost"] for u in usages]),
            "billed_complete": all(u["cost_complete"] for u in usages),
            "cost_min": min((u["cost"] for u in usages if u["cost"] is not None), default=None),
            "cost_max": max((u["cost"] for u in usages if u["cost"] is not None), default=None),
        }
        if agent == "web":
            measure["searches"] = _mean([r["probe"]["search_calls"] for r in records])
        if agent == "code":
            measure["reads"] = _mean([r["probe"]["reads"] for r in records])
        if agent == "exercises":
            # La entrada no depende del numero de candidatos; la salida si. Se mide por candidato.
            counts = [by_id[r["id"]]["count"] for r in records]
            measure["output_tokens_per_candidate"] = _mean([u["output_tokens"] / n for u, n in zip(usages, counts)])
            measure["prompt_cost"] = _mean([u["prompt_cost"] for u in usages])
            measure["completion_cost_per_candidate"] = _mean(
                [None if u["completion_cost"] is None else u["completion_cost"] / n for u, n in zip(usages, counts)])
            measure["candidates_measured"] = sorted(set(counts))
        out[agent] = measure
    return out


# ------------------------------------------------------------- coste medio --

def agent_cost(measure: dict, agent: str, prices: dict, kind: str, candidates: int = 5) -> dict:
    """Coste medio de una llamada completa del agente.

    `measured`: el coste facturado por el proveedor si lo informo (y, si no, el
    precio de lista del modelo de produccion por los tokens medidos).
    `reference`: los mismos tokens con el precio del modelo de referencia.
    `fallback_min` / `fallback_max`: los mismos tokens con el precio del modelo de
    respaldo en el proveedor de inferencia mas barato / mas caro.
    """
    if agent == "exercises":
        tokens_in = measure["input_tokens"]
        tokens_out = measure["output_tokens_per_candidate"] * candidates
    else:
        tokens_in, tokens_out = measure["input_tokens"], measure["output_tokens"]

    if kind == "reference":
        model = price_table.agent_model(prices, "reference", agent)
        return {"cost": price_table.token_cost(prices, model, tokens_in, tokens_out), "source": f"precio de {model}"}
    if kind in ("fallback_min", "fallback_max"):
        entry = price_table.fallback_price(prices, agent, kind.split("_")[1])
        return {"cost": (tokens_in * entry["input_per_m"] + tokens_out * entry["output_per_m"]) / 1_000_000,
                "source": f"respaldo {entry['model']} ({entry['provider']})"}

    if agent == "exercises" and measure.get("prompt_cost") is not None and measure.get("completion_cost_per_candidate") is not None:
        return {"cost": measure["prompt_cost"] + candidates * measure["completion_cost_per_candidate"], "source": "facturado"}
    if agent != "exercises" and measure["billed_cost"] is not None:
        return {"cost": measure["billed_cost"], "source": "facturado" if measure["billed_complete"] else "facturado (incompleto)"}
    model = price_table.agent_model(prices, "production", agent)
    return {"cost": price_table.token_cost(prices, model, tokens_in, tokens_out), "source": f"precio de lista de {model}"}


def _stage(name: str, cost: dict | None) -> tuple[str, float | None]:
    return name, None if cost is None else cost["cost"]


def operations(measures: dict, prices: dict, kind: str = "measured", candidates: int = 5) -> dict:
    """Las cuatro operaciones del sistema (mas sus variantes con acierto de memoria)."""
    costs = {a: (None if measures.get(a) is None else agent_cost(measures[a], a, prices, kind, candidates))
             for a in AGENTS}
    plan = price_table.tavily_plan(prices, "payg")
    marginal = None
    if measures.get("web") is not None and plan["extra_credit_price"] is not None:
        marginal = measures["web"]["searches"] * plan["credits_per_search"] * plan["extra_credit_price"]

    def compose(stages: list[str], tavily: bool = False) -> dict:
        missing = [s for s in stages if costs[s] is None]
        parts = {s: (None if costs[s] is None else costs[s]["cost"]) for s in stages}
        if tavily and "web" in stages:
            parts["tavily_marginal"] = marginal
        incomplete = bool(missing) or (tavily and "web" in stages and marginal is None)
        known = [v for v in parts.values() if v is not None]
        total = None if missing else sum(known)
        return {
            "cost": total,
            "breakdown": parts,
            "share": {k: (v / total if total and v is not None else None) for k, v in parts.items()},
            "missing": missing,
            "incomplete": incomplete,
        }

    return {
        "validate_technology": compose(["validator"]),
        "evaluate_answer": compose(["evaluator", "reviewer"]),
        "generate_without_repo": compose(["validator", "web", "exercises"], tavily=True),
        "generate_with_repo": compose(["validator", "web", "code", "exercises"], tavily=True),
        "generate_memory_hit": compose(["validator", "exercises"]),
    }


# ------------------------------------------------------------------ campana --

def generations_needed(saved: int, candidates: int, save_rate: float) -> int:
    """Generaciones para obtener `saved` ejercicios guardados: cada una produce
    `candidates` candidatos y solo se guarda `save_rate` de ellos."""
    return math.ceil(saved / (candidates * save_rate))


# Valores "redondos" para un tope de presupuesto de una clave de LiteLLM.
CAP_STEPS = (5, 10, 20, 50, 100, 200, 500, 1000)


def recommended_cap(peak: float, margin: float) -> float:
    """Menor tope redondo que cubre el pico de la clave mas cargada con `margin`
    veces de holgura. Es un dimensionado, no una medida de seguridad: el tope real
    lo decide quien lo aplica (para un cliente, subirlo o quitarlo)."""
    needed = peak * margin
    return next((step for step in CAP_STEPS if step >= needed), math.ceil(needed))


def memory_misses(generations: float, keys: int) -> int:
    """Fallos de memoria: como mucho una vez por clave distinta y nunca mas que generaciones."""
    return min(math.ceil(generations), keys)


def _tavily_cost(prices: dict, credits: float, months: int, plan_name: str) -> dict:
    plan = price_table.tavily_plan(prices, plan_name)
    excess = max(0.0, credits - plan["included_credits"])
    if excess > 0 and plan["extra_credit_price"] is None:
        return {"plan": plan_name, "credits": credits, "included": plan["included_credits"], "sufficient": False,
                "cost": None}
    cost = plan["monthly_fee"] * months + excess * (plan["extra_credit_price"] or 0)
    return {"plan": plan_name, "credits": credits, "included": plan["included_credits"], "excess": excess,
            "sufficient": True, "cost": cost}


def campaign(level: str, teams: int, measures: dict, assumptions: dict, prices: dict, kind: str = "measured") -> dict:
    """Coste de la campana de un nivel de uso: generacion inicial (mes 1),
    resolucion por los juniors (dos semanas, mes 2) y regimen (un ano)."""
    a = lambda name: value(assumptions, name)  # noqa: E731
    ops = operations(measures, prices, kind, a("candidates_per_generation"))
    missing = sorted({m for op in ops.values() if op["cost"] is None for m in op["missing"]})
    if missing:
        return {"computable": False, "missing": missing}

    cost = {agent: agent_cost(measures[agent], agent, prices, kind, a("candidates_per_generation"))["cost"]
            for agent in AGENTS}
    eval_cost = cost["evaluator"] + cost["reviewer"]

    generations = generations_needed(a("saved_exercises"), a("candidates_per_generation"), a("save_rate"))
    with_repo = math.ceil(generations * a("with_repo_share"))
    web_keys = a("technologies_per_project")
    code_keys = a("repositories_per_project") * a("technologies_per_project")

    def generation_phase(multiplier: int) -> dict:
        web_miss = memory_misses(generations, web_keys * multiplier)
        code_miss = memory_misses(with_repo, code_keys * multiplier)
        per_agent = {
            "validator": generations * cost["validator"],
            "exercises": generations * cost["exercises"],
            "web": web_miss * cost["web"],
            "code": code_miss * cost["code"],
        }
        credits = web_miss * measures["web"]["searches"] * prices["tavily"]["credits_per_search"]
        return {"web_misses": web_miss, "code_misses": code_miss, "per_agent": per_agent,
                "llm_cost": sum(per_agent.values()), "tavily_credits": credits}

    base = generation_phase(1)
    juniors, per_junior = a("juniors_per_team"), a("exercises_per_junior")
    evaluations = juniors * per_junior
    resolution_agents = {"evaluator": evaluations * cost["evaluator"], "reviewer": evaluations * cost["reviewer"]}
    resolution_cost = sum(resolution_agents.values())

    # Regimen (un ano, por equipo): los juniors nuevos resuelven el catalogo y el tech lead anade ejercicios
    # nuevos, que tambien resuelven los juniors del equipo. La memoria caduca (esporadico): cada generacion falla.
    new_gen = generations_needed(a("new_exercises_per_year"), a("candidates_per_generation"), a("save_rate"))
    miss_all = not a("regime_memory_hit")
    regime_web = new_gen if miss_all else 0
    regime_code = math.ceil(new_gen * a("with_repo_share")) if miss_all else 0
    regime_generation = (new_gen * (cost["validator"] + cost["exercises"]) + regime_web * cost["web"]
                         + regime_code * cost["code"])
    regime_evals = (a("new_juniors_per_year") * a("saved_exercises") + juniors * a("new_exercises_per_year")) * eval_cost
    regime_cost = regime_generation + regime_evals
    regime_credits = regime_web * measures["web"]["searches"] * prices["tavily"]["credits_per_search"]

    team_total = base["llm_cost"] + resolution_cost + regime_cost
    llm_campaign = teams * (base["llm_cost"] + resolution_cost)

    # Ventana de 30 dias mas cargada de cada clave de LiteLLM (claves de la organizacion): la generacion cae
    # en el mes 1 y la resolucion en el mes 2, sin solaparse.
    peak = {agent: teams * base["per_agent"][agent] for agent in GENERATION_AGENTS}
    peak.update({agent: teams * resolution_agents[agent] for agent in EVALUATION_AGENTS})
    budget = a("key_budget_usd_30d")
    over_budget = sorted(agent for agent, c in peak.items() if c > budget)
    margin = a("key_cap_margin")
    cap = recommended_cap(max(peak.values()), margin)

    generation_cost = base["llm_cost"]
    return {
        "computable": True,
        "teams": teams,
        "generations_per_tech_lead": generations,
        "generations_with_repo": with_repo,
        "evaluations_per_team": evaluations,
        "memory": {"web_misses": base["web_misses"], "code_misses": base["code_misses"],
                   "web_keys": web_keys, "code_keys": code_keys},
        "phases_per_team": {"generation": generation_cost, "resolution": resolution_cost, "regime_year": regime_cost},
        "campaign_llm_cost": llm_campaign,
        "share": {"generation": teams * generation_cost / llm_campaign if llm_campaign else None,
                  "evaluation": teams * resolution_cost / llm_campaign if llm_campaign else None},
        "peak_30d_per_key": peak,
        "keys_over_budget": over_budget,
        "recommended_key_cap": {"usd_30d": cap, "margin": margin, "most_loaded_key": max(peak, key=peak.get),
                                "peak": max(peak.values())},
        "tavily": {
            "campaign": {name: _tavily_cost(prices, teams * base["tavily_credits"], 1, name)
                         for name in prices["tavily"]["plans"]},
            "regime_year_credits": teams * regime_credits,
        },
        "sensitivity": {
            str(m): {"web_misses": generation_phase(m)["web_misses"], "code_misses": generation_phase(m)["code_misses"],
                     "generation_cost_per_team": generation_phase(m)["llm_cost"],
                     "tavily_credits": teams * generation_phase(m)["tavily_credits"]}
            for m in a("key_multipliers")
        },
        "unit_costs": {
            "per_saved_exercise": generation_cost / a("saved_exercises"),
            "per_evaluation": eval_cost,
            "per_junior_trained": per_junior * eval_cost + generation_cost / juniors,
        },
        "team_total_first_year": team_total,
    }


# ------------------------------------------------------------------ informe --

def fallback_section(measures: dict, assumptions: dict, prices: dict, levels: dict, measured: dict,
                     candidates: int) -> dict:
    """Coste con el modelo de respaldo, con los mismos tokens medidos: por
    operacion y por campana (rango entre el proveedor mas barato y el mas caro) y
    ponderado por la fraccion de llamadas que cae al respaldo. La fraccion real
    no se mide: son escenarios."""
    shares = value(assumptions, "fallback_shares")
    ops = {bound: operations(measures, prices, f"fallback_{bound}", candidates) for bound in ("min", "max")}
    section = {"shares": shares, "operations": ops, "campaign": {}, "weighted": {},
               "providers": {a: {b: price_table.fallback_price(prices, a, b) for b in ("min", "max")} for a in AGENTS}}
    for level, teams in levels.items():
        low = campaign(level, teams, measures, assumptions, prices, "fallback_min")
        high = campaign(level, teams, measures, assumptions, prices, "fallback_max")
        section["campaign"][level] = {"min": low, "max": high}
        base = measured[level]
        if base["computable"] and low["computable"] and high["computable"]:
            section["weighted"][level] = {
                str(f): {"min": (1 - f) * base["campaign_llm_cost"] + f * low["campaign_llm_cost"],
                         "max": (1 - f) * base["campaign_llm_cost"] + f * high["campaign_llm_cost"]}
                for f in shares}
    return section


def build_cost_report(cases: dict[str, list], datasets: dict, prices: dict, assumptions: dict) -> dict:
    measures = measure_agents(cases, datasets)
    missing = [a for a in AGENTS if measures[a] is None]
    candidates = value(assumptions, "candidates_per_generation")
    levels = {level: value(assumptions, f"teams_{level}") for level in LEVELS}

    measured = {level: campaign(level, teams, measures, assumptions, prices, "measured") for level, teams in levels.items()}
    reference = {level: campaign(level, teams, measures, assumptions, prices, "reference") for level, teams in levels.items()}
    comparison = {}
    for level in LEVELS:
        m, r = measured[level], reference[level]
        if m["computable"] and r["computable"]:
            comparison[level] = {"measured": m["campaign_llm_cost"], "reference": r["campaign_llm_cost"],
                                 "factor": r["campaign_llm_cost"] / m["campaign_llm_cost"] if m["campaign_llm_cost"] else None}

    crosscheck = {}
    for agent in AGENTS:
        measure = measures[agent]
        if measure is None or measure["billed_cost"] is None:
            continue
        model = price_table.agent_model(prices, "production", agent)
        if agent == "exercises":
            continue  # su coste facturado por llamada depende del numero de candidatos del caso
        listed = price_table.token_cost(prices, model, measure["input_tokens"], measure["output_tokens"])
        crosscheck[agent] = {"billed": measure["billed_cost"], "list_price": listed,
                             "ratio": measure["billed_cost"] / listed if listed else None}

    fallback = fallback_section(measures, assumptions, prices, levels, measured, candidates)

    return {
        "currency": prices["currency"],
        "prices_fetched": prices["fetched"],
        "candidates_per_generation": candidates,
        "measures": measures,
        "missing_agents": missing,
        "operations": operations(measures, prices, "measured", candidates),
        "operations_reference": operations(measures, prices, "reference", candidates),
        "campaign": measured,
        "campaign_reference": reference,
        "reference_comparison": comparison,
        "fallback": fallback,
        "crosscheck": crosscheck,
        "assumptions": assumptions,
    }


def _usd(v: float | None, digits: int = 4) -> str:
    return "n/d" if v is None else f"{v:,.{digits}f}"


def render_markdown(r: dict) -> str:
    out = [f"# Costes ({r['currency']}; precios de {r['prices_fetched']})", ""]
    if r["missing_agents"]:
        out += [f"> **Faltan mediciones de:** {', '.join(r['missing_agents'])}. Las operaciones y campanas que dependen de ellos no se pueden calcular.", ""]

    out += ["## Medicion por agente (media por llamada completa)", "",
            "| Agente | Casos | Tokens entrada | Tokens salida | Razonamiento | Coste medio facturado | Min - max |", "|---|---|---|---|---|---|---|"]
    for agent in AGENTS:
        m = r["measures"][agent]
        if m is None:
            out.append(f"| {agent} | 0 | n/d | n/d | n/d | n/d | n/d |")
            continue
        out.append(f"| {agent} | {m['cases']} | {m['input_tokens']:.0f} | {m['output_tokens']:.0f} | "
                   f"{'n/d' if m['reasoning_tokens'] is None else format(m['reasoning_tokens'], '.0f')} | "
                   f"{_usd(m['billed_cost'], 6)}{'' if m['billed_complete'] else ' (incompleto)'} | "
                   f"{_usd(m['cost_min'], 6)} - {_usd(m['cost_max'], 6)} |")

    out += ["", "El razonamiento esta incluido en los tokens de salida y se factura como salida.", "",
            f"## Coste por operacion (generar con {r['candidates_per_generation']} candidatos)", "",
            "| Operacion | Coste | Desglose |", "|---|---|---|"]
    names = {"validate_technology": "Validar una tecnologia", "evaluate_answer": "Evaluar una respuesta",
             "generate_without_repo": "Generar sin repositorio", "generate_with_repo": "Generar con repositorio",
             "generate_memory_hit": "Generar con acierto de memoria"}
    for key, label in names.items():
        op = r["operations"][key]
        if op["cost"] is None:
            out.append(f"| {label} | no calculable | falta: {', '.join(op['missing'])} |")
            continue
        parts = ", ".join(f"{k} {_usd(v, 6)} ({'n/d' if op['share'][k] is None else format(op['share'][k], '.0%')})"
                          for k, v in op["breakdown"].items())
        out.append(f"| {label} | {_usd(op['cost'], 6)}{' (incompleto)' if op['incomplete'] else ''} | {parts} |")
    out.append("")
    out.append("`tavily_marginal` valora cada busqueda al precio del credito adicional; la cuota real del plan se reparte en la campana.")

    for level in LEVELS:
        c = r["campaign"][level]
        out += ["", f"## Campana - nivel {level}", ""]
        if not c["computable"]:
            out.append(f"No calculable: faltan mediciones de {', '.join(c['missing'])}.")
            continue
        u = c["unit_costs"]
        out += [
            f"- Equipos: {c['teams']}. Generaciones por tech lead: {c['generations_per_tech_lead']} "
            f"({c['generations_with_repo']} con repositorio). Evaluaciones por equipo: {c['evaluations_per_team']}.",
            f"- Fallos de memoria por equipo: web {c['memory']['web_misses']} (de {c['memory']['web_keys']} claves), "
            f"codigo {c['memory']['code_misses']} (de {c['memory']['code_keys']} claves).",
            f"- Coste por equipo: generacion {_usd(c['phases_per_team']['generation'])}, resolucion "
            f"{_usd(c['phases_per_team']['resolution'])}, regimen anual {_usd(c['phases_per_team']['regime_year'])}.",
            f"- **Campana (modelos, todos los equipos): {_usd(c['campaign_llm_cost'])}** - generacion "
            f"{c['share']['generation']:.0%}, evaluacion {c['share']['evaluation']:.0%}.",
            f"- Costes unitarios: por ejercicio guardado {_usd(u['per_saved_exercise'], 6)}, por evaluacion "
            f"{_usd(u['per_evaluation'], 6)}, por junior formado {_usd(u['per_junior_trained'])}.",
            f"- Pico de 30 dias por clave (presupuesto {value(r['assumptions'], 'key_budget_usd_30d')}): "
            + ", ".join(f"{k} {_usd(v)}" for k, v in c["peak_30d_per_key"].items())
            + (f". **Superan el presupuesto: {', '.join(c['keys_over_budget'])}.**" if c["keys_over_budget"] else ". Ninguna lo supera."),
            f"- Tope por clave que cubre el pico de la clave mas cargada ({c['recommended_key_cap']['most_loaded_key']}, "
            f"{_usd(c['recommended_key_cap']['peak'])}) con {c['recommended_key_cap']['margin']:g}x de holgura: "
            f"**{c['recommended_key_cap']['usd_30d']:g} USD / 30 dias** (dimensionado; el tope real es una decision de quien lo aplica).",
        ]
        for plan, t in c["tavily"]["campaign"].items():
            if not t["sufficient"]:
                out.append(f"- Tavily, plan {plan}: {t['credits']:.0f} creditos; **el plan no basta** ({t['included']} incluidos y sin exceso).")
            else:
                out.append(f"- Tavily, plan {plan}: {t['credits']:.0f} creditos de {t['included']} incluidos -> {_usd(t['cost'], 2)} (mes 1).")
        out.append(f"- Creditos de Tavily en regimen: {c['tavily']['regime_year_credits']:.0f} al ano.")
        out.append("- Sensibilidad al numero de claves de memoria: " + "; ".join(
            f"x{m}: web {s['web_misses']}, codigo {s['code_misses']}, generacion por equipo {_usd(s['generation_cost_per_team'])}"
            for m, s in c["sensitivity"].items()))

    fb = r["fallback"]
    out += ["", "## Sensibilidad al modelo de respaldo (mismos tokens)", "",
            "Si el modelo primario falla, LiteLLM reintenta con el respaldo de Hugging Face. El precio depende del "
            "proveedor de inferencia al que enrute: se muestra el rango. **La fraccion real de llamadas que cae al "
            "respaldo no se mide** (el alias no distingue el modelo que contesto): son escenarios, no una prediccion.", "",
            "| Agente | Respaldo | Proveedor mas barato (entrada / salida) | Proveedor mas caro (entrada / salida) |", "|---|---|---|---|"]
    for agent in AGENTS:
        lo, hi = fb["providers"][agent]["min"], fb["providers"][agent]["max"]
        out.append(f"| {agent} | {lo['model']} | {lo['provider']} {lo['input_per_m']} / {lo['output_per_m']} | "
                   f"{hi['provider']} {hi['input_per_m']} / {hi['output_per_m']} |")
    out += ["", "| Operacion | Medido | Respaldo (min - max) |", "|---|---|---|"]
    for key, label in names.items():
        measured_cost = r["operations"][key]["cost"]
        low, high = fb["operations"]["min"][key]["cost"], fb["operations"]["max"][key]["cost"]
        if measured_cost is None:
            out.append(f"| {label} | no calculable | no calculable |")
        else:
            out.append(f"| {label} | {_usd(measured_cost, 6)} | {_usd(low, 6)} - {_usd(high, 6)} |")
    if fb["weighted"]:
        out += ["", "| Nivel | " + " | ".join(f"{float(f):.0%} al respaldo" for f in fb["shares"]) + " |",
                "|---|" + "---|" * len(fb["shares"])]
        for level, by_share in fb["weighted"].items():
            out.append(f"| {level} | " + " | ".join(
                f"{_usd(by_share[str(f)]['min'])} - {_usd(by_share[str(f)]['max'])}" for f in fb["shares"]) + " |")
    else:
        out += ["", "Campana con respaldo: no calculable hasta tener la medicion de todos los agentes."]

    out += ["", "## Comparativa con el modelo de referencia (mismos tokens)", ""]
    if r["reference_comparison"]:
        out += ["| Nivel | Medido | Referencia | Factor |", "|---|---|---|---|"]
        for level, cmp in r["reference_comparison"].items():
            out.append(f"| {level} | {_usd(cmp['measured'])} | {_usd(cmp['reference'])} | x{_usd(cmp['factor'], 1)} |")
    else:
        out.append("No calculable hasta tener la medicion de todos los agentes.")
    out += ["", "El modelo de referencia es una cota inferior: otro modelo gastaria otros tokens (mas o menos razonamiento).", ""]

    if r["crosscheck"]:
        out += ["## Comprobacion cruzada: facturado frente a precio de lista", "",
                "| Agente | Facturado | Precio de lista | Razon |", "|---|---|---|---|"]
        for agent, c in r["crosscheck"].items():
            out.append(f"| {agent} | {_usd(c['billed'], 6)} | {_usd(c['list_price'], 6)} | {_usd(c['ratio'], 2)} |")
        out.append("")

    out += ["## Supuestos (hipotesis salvo indicacion)", "", "| Supuesto | Valor | Origen |", "|---|---|---|"]
    for name, entry in r["assumptions"].items():
        out.append(f"| {name} | {entry['value']} | {entry['origin']} |")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("reports", nargs="+", help="informe(s) JSON del modo real")
    parser.add_argument("--prices", default=str(price_table.PRICES_PATH))
    parser.add_argument("--assumptions", default=str(ASSUMPTIONS_PATH))
    parser.add_argument("--out-dir", default=str(RESULTS_DIR))
    args = parser.parse_args(argv)
    try:
        merged = merge_reports([Path(p) for p in args.reports])
        result = build_cost_report(merged["cases"], dataset.load_all(), price_table.load_prices(Path(args.prices)),
                                   load_assumptions(Path(args.assumptions)))
    except (CostError, price_table.PriceError, dataset.DatasetError, OSError, KeyError) as exc:
        print(f"no se pueden calcular los costes: {exc}", file=sys.stderr)
        return 2
    result["reports"] = merged["reports"]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.reports[-1]).stem
    (out_dir / f"{stem}-costes.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = render_markdown(result)
    (out_dir / f"{stem}-costes.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"Informe: {out_dir / (stem + '-costes.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
