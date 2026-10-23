"""Orquestador de la suite de evaluacion de agentes.

Uso (desde la raiz del repositorio):

    python -m evals.run                       # modo simulado, los cuatro agentes
    python -m evals.run --agents evaluator    # solo uno
    python -m evals.run --mode real           # modelos reales via LiteLLM (cuesta dinero)

Lanza un subproceso por agente (`evals/agent_runner.py`, con el entorno de
dependencias de ese agente), agrega los resultados, calcula las metricas y
escribe el informe en `evals/results/`.

Codigo de salida:
  0  todo bien (en modo real, tambien aunque una metrica sea mala: solo mide)
  1  modo simulado con una invariante rota
  2  la propia ejecucion fallo (dataset invalido, agente no ejecutable, ...)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from evals import dataset, report

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
AGENTS = ("evaluator", "reviewer", "validator", "exercises")
_MARKER = "EVALS_JSON:"
_TIMEOUT_SECONDS = 900


def agent_python(agent: str, overrides: dict[str, str]) -> str:
    """Interprete con las dependencias del agente: el indicado con
    `--python`, el `.venv` del propio agente o, en su defecto, el actual."""
    if agent in overrides:
        return overrides[agent]
    for candidate in (AGENTS_DIR / agent / ".venv" / "Scripts" / "python.exe",
                      AGENTS_DIR / agent / ".venv" / "bin" / "python"):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def run_agent(agent: str, mode: str, python: str, datasets_dir: Path, limit_per_set: int) -> dict:
    cmd = [python, "-m", "evals.agent_runner", "--agent", agent, "--mode", mode,
           "--datasets-dir", str(datasets_dir)]
    if limit_per_set:
        cmd += ["--limit-per-set", str(limit_per_set)]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REPO_ROOT), env.get("PYTHONPATH", "")]))
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(cmd, cwd=AGENTS_DIR / agent, env=env, capture_output=True,
                              text=True, encoding="utf-8", timeout=_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return {"not_executed": f"supera el limite de {_TIMEOUT_SECONDS}s"}
    payload = None
    for line in proc.stdout.splitlines():
        if line.startswith(_MARKER):
            payload = json.loads(line[len(_MARKER):])
    if payload is None:
        tail = (proc.stderr.strip().splitlines() or ["sin salida"])[-1]
        return {"not_executed": f"el proceso termino con codigo {proc.returncode} sin resultados ({tail})"}
    if "fatal" in payload:
        return {"not_executed": payload["fatal"]}
    return {"cases": payload["cases"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=("simulated", "real"), default="simulated")
    parser.add_argument("--agents", default=",".join(AGENTS), help="lista separada por comas")
    parser.add_argument("--datasets-dir", default=str(dataset.DATASETS_DIR))
    parser.add_argument("--results-dir", default=str(RESULTS_DIR))
    parser.add_argument("--python", action="append", default=[], metavar="AGENTE=RUTA",
                        help="interprete a usar para un agente (repetible)")
    parser.add_argument("--limit-per-set", type=int, default=0,
                        help="maximo de casos por conjunto y agente (0 = todos); util en modo real para acotar el coste")
    args = parser.parse_args(argv)

    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    unknown = [a for a in agents if a not in AGENTS]
    if unknown:
        print(f"agente(s) desconocido(s): {unknown}; validos: {list(AGENTS)}", file=sys.stderr)
        return 2
    overrides = dict(item.split("=", 1) for item in args.python if "=" in item)

    try:
        data = dataset.load_all(Path(args.datasets_dir))
    except dataset.DatasetError as exc:
        print(f"dataset invalido: {exc}", file=sys.stderr)
        return 2

    runs = {}
    for agent in agents:
        print(f"-> {agent} ({args.mode})...", file=sys.stderr)
        runs[agent] = run_agent(agent, args.mode, agent_python(agent, overrides),
                                Path(args.datasets_dir), args.limit_per_set)

    result = report.build_report(args.mode, runs, data)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = results_dir / f"{stamp}-{args.mode}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(report.render_summary(result))
    print(f"\nInforme: {path}")

    if result["not_executed"]:
        return 2
    if args.mode == "simulated" and result["invariants"]["violations"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
