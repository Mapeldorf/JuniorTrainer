"""Juez offline de calidad pedagogica del contenido (capstone §5.6).

Instrumento de medida, NO un agente ni un servicio A2A: puntua ejercicios con una
rubrica de cinco criterios usando un modelo frontier (alias `judge` de LiteLLM)
distinto de los cuatro de produccion, y se calibra contra puntuaciones humanas.
Solo biblioteca estandar; llama a LiteLLM por HTTP con su **propia virtual key**
(`AGENT_JUDGE_LITELLM_KEY`), como cualquier otro consumidor del proxy: nunca con
la master key de administracion.

Uso (desde la raiz del repositorio):

    python -m evals.judge                 # puntua y, si hay puntuaciones humanas, calibra
    python -m evals.judge --dataset evals/datasets/judge.jsonl

Change `juez-contenido`. No escribe en la base de datos ni toca al alumno.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from evals import judge_dataset
from evals.judge_dataset import CRITERIA, DEBUG_ONLY
from evals.metrics import cohen_kappa

RESULTS_DIR = Path(__file__).resolve().parent / "results"
SCORE_LABELS = ("0", "1", "2")

_SYSTEM_PROMPT = (
    "Eres un juez que evalua la calidad pedagogica de un ejercicio de programacion "
    "para desarrolladores junior recien incorporados a un proyecto. Puntua cada "
    "criterio de 0 a 2 (0 = no lo cumple, 1 = parcialmente, 2 = lo cumple):\n"
    "- unicidad_de_concepto: el enunciado trata UN SOLO concepto, sin encadenar preguntas.\n"
    "- autosuficiencia: es resoluble solo con el enunciado y el codigo de apoyo entregado.\n"
    "- nivel: es un ejercicio de junior recien incorporado, no de senior (nada de refactorizar, "
    "redisenar ni recorrer varios ficheros).\n"
    "- calidad_del_fallo: SOLO para tipo 'debug'; el fragmento contiene EXACTAMENTE UN fallo, "
    "real y localizable. Para 'knowledge' responde null.\n"
    "- utilidad_de_la_justificacion: la respuesta esperada dice que es correcto o que esta mal "
    "y por que, en lugar de explicar teoria.\n"
    "Responde EXCLUSIVAMENTE con un objeto JSON con esta forma: "
    '{"scores": {"unicidad_de_concepto": 0, "autosuficiencia": 0, "nivel": 0, '
    '"calidad_del_fallo": 0, "utilidad_de_la_justificacion": 0}, "justification": "..."}. '
    "El valor de 'calidad_del_fallo' es null si el tipo es 'knowledge'. La justificacion "
    "es obligatoria y no vacia."
)


def _user_message(case: dict) -> str:
    parts = [f"Tipo: {case['type']}", f"Enunciado: {case['statement']}"]
    code = case.get("code") or []
    if code:
        blocks = "\n\n".join(f"[{b['file']}]\n{b['code']}" for b in code)
        parts.append(f"Codigo de apoyo:\n{blocks}")
    else:
        parts.append("Codigo de apoyo: (ninguno)")
    parts.append(f"Respuesta esperada: {case['expected_answer']}")
    return "\n".join(parts)


def _parse(text: str, exercise_type: str) -> dict | None:
    """Valida el JSON de la rubrica. `None` si no cumple (para reintentar)."""
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(obj, dict):
        return None
    scores, justification = obj.get("scores"), obj.get("justification")
    if not isinstance(scores, dict) or not isinstance(justification, str) or not justification.strip():
        return None
    clean: dict[str, int | None] = {}
    for criterion in CRITERIA:
        value = scores.get(criterion)
        if criterion == DEBUG_ONLY and exercise_type == "knowledge":
            if value is not None:
                return None
            clean[criterion] = None
            continue
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2:
            return None
        clean[criterion] = value
    return {"scores": clean, "justification": justification.strip()}


def call_judge(base_url: str, master_key: str, model: str, system: str, user: str, timeout: float) -> str:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {master_key}"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def judge_case(case: dict, invoke) -> dict:
    """Puntua un ejercicio con `invoke(system, user) -> texto crudo`. Reintenta una
    sola vez si la salida no cumple la rubrica (misma regla que los agentes)."""
    record = {"id": case["id"], "type": case["type"], "outcome": "ok", "error": None,
              "scores": None, "justification": None, "calls": 0}
    user = _user_message(case)
    for _ in range(2):
        record["calls"] += 1
        try:
            raw = invoke(_SYSTEM_PROMPT, user)
        except Exception as exc:  # noqa: BLE001 - se clasifica y se informa
            record.update(outcome="infra_error", error=f"{type(exc).__name__}: {exc}"[:300])
            return record
        parsed = _parse(raw, case["type"])
        if parsed is not None:
            record.update(scores=parsed["scores"], justification=parsed["justification"])
            return record
    record.update(outcome="not_judged", error="la salida no cumple la rubrica tras el reintento")
    return record


def calibration(cases: list[dict], human: dict) -> dict | None:
    """κ de Cohen por criterio entre el juez y el humano. `None` si no hay
    puntuaciones humanas utilizables."""
    if not human:
        return None
    per_criterion: dict[str, dict] = {}
    all_pairs: list[tuple[str, str]] = []
    for criterion in CRITERIA:
        pairs = []
        for case in cases:
            if case.get("scores") is None:
                continue
            judge_score = case["scores"].get(criterion)
            human_score = human.get(case["id"], {}).get(criterion)
            if judge_score is None or human_score is None:
                continue
            pairs.append((str(human_score), str(judge_score)))
        all_pairs += pairs
        per_criterion[criterion] = {"pairs": len(pairs), "kappa": cohen_kappa(pairs, SCORE_LABELS)}
    return {
        "cases_with_human": len({case["id"] for case in cases if case.get("scores") is not None and human.get(case["id"])}),
        "criteria": per_criterion,
        "overall": {"pairs": len(all_pairs), "kappa": cohen_kappa(all_pairs, SCORE_LABELS)},
    }


def build_report(cases: list[dict], human: dict, model: str, now: datetime | None = None) -> dict:
    means = {}
    for criterion in CRITERIA:
        values = [c["scores"][criterion] for c in cases
                  if c.get("scores") and c["scores"].get(criterion) is not None]
        means[criterion] = sum(values) / len(values) if values else None
    return {
        "model": model,
        "rubric": list(CRITERIA),
        "generated_at": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
        "cases": cases,
        "means": means,
        "not_judged": [c["id"] for c in cases if c["outcome"] != "ok"],
        "calibration": calibration(cases, human),
    }


def _fmt(value) -> str:
    return "n/d" if value is None else f"{value:.3f}"


def render_summary(report: dict) -> str:
    lines = [f"Juez de contenido - modelo {report['model']} - {report['generated_at']}",
             f"{len(report['cases'])} ejercicios, {len(report['not_judged'])} no juzgados"]
    for criterion in report["rubric"]:
        lines.append(f"  {criterion}: media {_fmt(report['means'].get(criterion))}")
    cal = report["calibration"]
    if cal is None:
        lines.append("  calibracion: n/d (sin puntuaciones humanas)")
    else:
        lines.append(f"  calibracion vs humano ({cal['cases_with_human']} ejercicios): "
                     f"global kappa {_fmt(cal['overall']['kappa'])}")
        for criterion, data in cal["criteria"].items():
            lines.append(f"    {criterion}: kappa {_fmt(data['kappa'])} ({data['pairs']} pares)")
    return "\n".join(lines)


def _preflight() -> tuple[str, str, str]:
    model = os.environ.get("JUDGE_MODEL", "").strip()
    judge_key = os.environ.get("AGENT_JUDGE_LITELLM_KEY", "").strip()
    base_url = os.environ.get("LITELLM_BASE_URL", "").strip()
    missing = [name for name, value in
               (("JUDGE_MODEL", model), ("AGENT_JUDGE_LITELLM_KEY", judge_key),
                ("LITELLM_BASE_URL", base_url)) if not value]
    if missing:
        raise SystemExit(f"faltan variables de entorno: {', '.join(missing)}")
    return model, judge_key, base_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Juez offline de calidad pedagogica (capstone 5.6)")
    parser.add_argument("--dataset", default=str(judge_dataset.JUDGE_DATASET))
    parser.add_argument("--human", default=str(judge_dataset.JUDGE_HUMAN))
    parser.add_argument("--results-dir", default=str(RESULTS_DIR))
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args(argv)

    try:
        cases = judge_dataset.load(Path(args.dataset))
        human = judge_dataset.load_human(Path(args.human))
    except judge_dataset.JudgeDatasetError as exc:
        print(f"dataset invalido: {exc}", file=sys.stderr)
        return 2

    model, judge_key, base_url = _preflight()

    def invoke(system: str, user: str) -> str:
        return call_judge(base_url, judge_key, model, system, user, args.timeout)

    judged = [judge_case(case, invoke) for case in cases]
    report = build_report(judged, human, model)

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = results_dir / f"{stamp}-judge.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(render_summary(report))
    print(f"\nInforme: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())