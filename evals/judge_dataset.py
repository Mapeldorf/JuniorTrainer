"""Carga y validacion del conjunto de calibracion del juez (capstone §5.6).

`evals/datasets/judge.jsonl`: una linea JSON por ejercicio a puntuar. La
puntuacion humana vive aparte (`evals/datasets/judge.human.json`) para que el
humano puntee a ciegas de la del juez (change `juez-contenido`). Solo biblioteca
estandar.
"""

import json
from pathlib import Path

DATASETS_DIR = Path(__file__).resolve().parent / "datasets"
JUDGE_DATASET = DATASETS_DIR / "judge.jsonl"
JUDGE_HUMAN = DATASETS_DIR / "judge.human.json"

EXERCISE_TYPES = ("knowledge", "debug")
CRITERIA = (
    "unicidad_de_concepto",
    "autosuficiencia",
    "nivel",
    "calidad_del_fallo",
    "utilidad_de_la_justificacion",
)
# Criterio que no aplica a los ejercicios de conocimiento.
DEBUG_ONLY = "calidad_del_fallo"


class JudgeDatasetError(ValueError):
    """Un ejercicio del conjunto o una puntuacion humana no cumple el formato."""


def _fail(case_id: str, field: str, reason: str):
    raise JudgeDatasetError(f"judge/{case_id}: campo '{field}': {reason}")


def load(path: Path = JUDGE_DATASET) -> list[dict]:
    if not path.is_file():
        raise JudgeDatasetError(f"no existe {path}")
    cases: list[dict] = []
    seen: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise JudgeDatasetError(f"judge: linea {line_number}: JSON invalido ({exc})") from exc
        case_id = case.get("id") if isinstance(case, dict) else None
        if not isinstance(case_id, str) or not case_id:
            raise JudgeDatasetError(f"judge: linea {line_number}: campo 'id': falta o no es texto")
        if case_id in seen:
            raise JudgeDatasetError(f"judge/{case_id}: campo 'id': identificador duplicado")
        seen.add(case_id)
        if case.get("type") not in EXERCISE_TYPES:
            _fail(case_id, "type", f"uno de {EXERCISE_TYPES}")
        if not isinstance(case.get("statement"), str) or not case["statement"].strip():
            _fail(case_id, "statement", "texto no vacio")
        if not isinstance(case.get("code"), list):
            _fail(case_id, "code", "lista")
        for block in case["code"]:
            if not isinstance(block, dict) or not isinstance(block.get("file"), str) or not isinstance(block.get("code"), str):
                _fail(case_id, "code", "cada bloque necesita 'file' y 'code' de tipo texto")
        if not isinstance(case.get("expected_answer"), str) or not case["expected_answer"].strip():
            _fail(case_id, "expected_answer", "texto no vacio")
        cases.append(case)
    if not cases:
        raise JudgeDatasetError("judge: el conjunto no tiene ningun caso")
    return cases


def load_human(path: Path = JUDGE_HUMAN) -> dict[str, dict[str, int | None]]:
    """Puntuaciones humanas por id y criterio. `{}` si el fichero no existe o solo
    trae comentarios (la calibracion se informa entonces como no disponible)."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise JudgeDatasetError("judge.human: se esperaba un objeto id -> criterio -> puntuacion")
    out: dict[str, dict[str, int | None]] = {}
    for case_id, scores in data.items():
        if case_id.startswith("_"):
            continue
        if not isinstance(scores, dict):
            _fail(case_id, "human", "se esperaba un objeto de criterio -> puntuacion")
        clean: dict[str, int | None] = {}
        for criterion, value in scores.items():
            if criterion not in CRITERIA:
                _fail(case_id, criterion, "criterio desconocido")
            if value is None:
                clean[criterion] = None
            elif isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2:
                _fail(case_id, criterion, "entero entre 0 y 2, o null")
            else:
                clean[criterion] = value
        out[case_id] = clean
    return out