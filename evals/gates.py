"""Aplica los umbrales del gate a un informe de evaluacion (capstone §5.3).

Funcion pura: recibe el informe que produce `evals/report.py` y la tabla de
umbrales, y devuelve que metricas incumplen y cuales quedaron sin evaluar. No
hace E/S; la unica lectura de fichero es la tabla. Change `evals-umbrales-gate`.
"""

import json
from pathlib import Path

THRESHOLDS = Path(__file__).resolve().parent / "thresholds.json"


class GatesError(ValueError):
    """La tabla de umbrales no cumple el formato."""


def load(path: Path = THRESHOLDS) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GatesError(f"thresholds: JSON invalido ({exc})") from exc
    if not isinstance(data, list):
        raise GatesError("thresholds: se esperaba una lista de entradas")
    for i, entry in enumerate(data):
        if not isinstance(entry, dict) or not isinstance(entry.get("agent"), str) or not isinstance(entry.get("metric"), str):
            raise GatesError(f"thresholds[{i}]: cada entrada necesita 'agent' y 'metric' de tipo texto")
        if ("min" in entry) == ("max" in entry):
            raise GatesError(f"thresholds[{i}] ({entry['metric']}): exactamente uno de 'min' o 'max'")
    return data


def _get(obj: dict, path: str):
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def evaluate(report: dict, thresholds: list[dict]) -> dict:
    """`{"failures": [...], "not_evaluated": [...], "evaluated": n}`.

    Una metrica sin casos (valor ausente o nulo) no se evalua: se informa aparte,
    no como fallo (spec `agent-evaluation`, escenario "Metrica sin casos")."""
    agents = report.get("agents", {})
    executed = [name for name, data in agents.items() if data.get("executed")]
    failures: list[dict] = []
    not_evaluated: list[dict] = []
    evaluated = 0
    for entry in thresholds:
        targets = executed if entry["agent"] == "*" else ([entry["agent"]] if entry["agent"] in executed else [])
        for agent in targets:
            value = _get(agents[agent], entry["metric"])
            if value is None:
                not_evaluated.append({"agent": agent, "metric": entry["metric"]})
                continue
            if "min" in entry:
                ok = value >= entry["min"]
            else:
                ok = value <= entry["max"]
            evaluated += 1
            if not ok:
                failures.append({"agent": agent, "metric": entry["metric"], "value": value,
                                 "min": entry.get("min"), "max": entry.get("max")})
    return {"failures": failures, "not_evaluated": not_evaluated, "evaluated": evaluated}


def render_summary(gate: dict) -> str:
    lines = [f"Gate de umbrales: {gate['evaluated']} metricas evaluadas, "
             f"{len(gate['failures'])} incumplidas, {len(gate['not_evaluated'])} sin casos"]
    for f in gate["failures"]:
        limit = f"min {f['min']}" if f["min"] is not None else f"max {f['max']}"
        lines.append(f"  INCUMPLE  {f['agent']}/{f['metric']}: {f['value']:.3f} ({limit})")
    for n in gate["not_evaluated"]:
        lines.append(f"  sin casos {n['agent']}/{n['metric']}")
    return "\n".join(lines)