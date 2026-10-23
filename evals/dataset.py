"""Carga y validacion del dataset dorado (`evals/datasets/*.jsonl`).

Una linea JSON por caso. La carga falla ANTES de ejecutar ningun agente si un
caso esta mal formado, nombrando conjunto, caso y campo (spec
`agent-evaluation`, requisito "Dataset dorado versionado en el repositorio").
Solo biblioteca estandar.
"""

import json
from pathlib import Path

DATASETS_DIR = Path(__file__).resolve().parent / "datasets"
SET_NAMES = ("generation", "evaluation", "validation", "adversarial")

VERDICTS = ("correct", "incomplete", "incorrect")
EXERCISE_TYPES = ("knowledge", "debug")
VALIDATION_CONTEXTS = ("catalog_entry", "generation")
ADVERSARIAL_TARGETS = ("evaluator", "reviewer", "validator")
SIM_OUTCOMES = ("ok", "contract_error")


class DatasetError(ValueError):
    """Un conjunto o un caso del dataset no cumple el formato."""


def _fail(set_name: str, case_id: str, field: str, reason: str):
    raise DatasetError(f"{set_name}/{case_id}: campo '{field}': {reason}")


def _is_str_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def _require(set_name: str, case: dict, field: str, check, reason: str):
    if field not in case:
        _fail(set_name, case.get("id", "?"), field, "falta")
    if not check(case[field]):
        _fail(set_name, case.get("id", "?"), field, reason)


def _optional(set_name: str, case: dict, field: str, check, reason: str):
    if field in case and not check(case[field]):
        _fail(set_name, case.get("id", "?"), field, reason)


def _check_sim(set_name: str, case: dict) -> None:
    """`sim` (respuestas crudas guionizadas) y `sim_expect` (que debe pasar
    con ese guion) solo se usan en modo simulado."""
    sim = case.get("sim")
    if sim is not None:
        ok = _is_str_list(sim) or (
            isinstance(sim, dict) and all(_is_str_list(v) for v in sim.values())
        )
        if not ok:
            _fail(set_name, case["id"], "sim", "debe ser una lista de textos o un objeto agente -> lista de textos")
    expect = case.get("sim_expect")
    if expect is not None:
        entries = expect.values() if isinstance(expect, dict) and "outcome" not in expect else [expect]
        for entry in entries:
            if not (
                isinstance(entry, dict)
                and entry.get("outcome") in SIM_OUTCOMES
                and isinstance(entry.get("calls"), int)
                and entry["calls"] >= 0
            ):
                _fail(
                    set_name,
                    case["id"],
                    "sim_expect",
                    f"cada entrada necesita 'outcome' ({', '.join(SIM_OUTCOMES)}) y 'calls' (entero >= 0)",
                )


def _validate_answer_case(set_name: str, case: dict) -> None:
    _require(set_name, case, "statement", lambda v: isinstance(v, str) and v.strip(), "texto no vacio")
    _require(set_name, case, "code", lambda v: isinstance(v, list), "lista")
    _optional(set_name, case, "expected_answer", lambda v: v is None or isinstance(v, str), "texto o null")
    _require(set_name, case, "student_answer", lambda v: isinstance(v, str) and v.strip(), "texto no vacio")
    _require(set_name, case, "label", lambda v: v in VERDICTS, f"uno de {VERDICTS}")
    _require(
        set_name, case, "proposed_justification",
        lambda v: isinstance(v, str) and v.strip(), "texto no vacio",
    )


def _validate_technology_case(set_name: str, case: dict) -> None:
    _require(set_name, case, "technologies", lambda v: _is_str_list(v) and len(v) > 0, "lista de textos no vacia")
    _require(set_name, case, "context", lambda v: v in VALIDATION_CONTEXTS, f"uno de {VALIDATION_CONTEXTS}")
    _require(set_name, case, "catalog", _is_str_list, "lista de textos")
    _require(set_name, case, "expect_valid", lambda v: isinstance(v, bool), "booleano")
    _optional(set_name, case, "expect_duplicates", _is_str_list, "lista de textos")
    _optional(set_name, case, "expect_prefilter", lambda v: isinstance(v, bool), "booleano")
    if case.get("expect_prefilter") and case["expect_valid"]:
        _fail(set_name, case["id"], "expect_prefilter", "un caso rechazado por el pre-filtro no puede esperar valid=true")


def _validate_generation_case(set_name: str, case: dict) -> None:
    _require(set_name, case, "type", lambda v: v in EXERCISE_TYPES, f"uno de {EXERCISE_TYPES}")
    _require(set_name, case, "count", lambda v: isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 5, "entero entre 1 y 5")
    _require(set_name, case, "technologies", lambda v: _is_str_list(v) and len(v) > 0, "lista de textos no vacia")
    _require(set_name, case, "web_result", lambda v: v is None or isinstance(v, dict), "objeto o null")
    _require(set_name, case, "code_result", lambda v: v is None or isinstance(v, dict), "objeto o null")
    _require(set_name, case, "saved_statements", _is_str_list, "lista de textos")
    _optional(set_name, case, "group", lambda v: isinstance(v, str) and v, "texto no vacio")
    _optional(set_name, case, "topics", _is_str_list, "lista de textos")
    if "sim" not in case and len(case.get("topics", [])) < case["count"]:
        _fail(set_name, case["id"], "topics", f"hacen falta al menos {case['count']} temas si el caso no trae 'sim'")


def _validate_case(set_name: str, case: dict) -> None:
    if set_name == "generation":
        _validate_generation_case(set_name, case)
    elif set_name == "evaluation":
        _validate_answer_case(set_name, case)
    elif set_name == "validation":
        _validate_technology_case(set_name, case)
    else:  # adversarial
        _require(set_name, case, "target", lambda v: v in ADVERSARIAL_TARGETS, f"uno de {ADVERSARIAL_TARGETS}")
        _require(set_name, case, "kind", lambda v: isinstance(v, str) and v, "texto no vacio")
        if case["target"] == "validator":
            _validate_technology_case(set_name, case)
        else:
            _validate_answer_case(set_name, case)
    _check_sim(set_name, case)


def load_set(set_name: str, directory: Path = DATASETS_DIR) -> list[dict]:
    path = directory / f"{set_name}.jsonl"
    if not path.is_file():
        raise DatasetError(f"{set_name}: no existe {path}")
    cases: list[dict] = []
    seen: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DatasetError(f"{set_name}: linea {line_number}: JSON invalido ({exc})") from exc
        if not isinstance(case, dict):
            raise DatasetError(f"{set_name}: linea {line_number}: se esperaba un objeto")
        if not isinstance(case.get("id"), str) or not case["id"]:
            raise DatasetError(f"{set_name}: linea {line_number}: campo 'id': falta o no es texto")
        if case["id"] in seen:
            raise DatasetError(f"{set_name}/{case['id']}: campo 'id': identificador duplicado")
        seen.add(case["id"])
        _validate_case(set_name, case)
        cases.append(case)
    if not cases:
        raise DatasetError(f"{set_name}: el conjunto no tiene ningun caso")
    return cases


def load_all(directory: Path = DATASETS_DIR) -> dict[str, list[dict]]:
    """Carga los cuatro conjuntos; falla en el primer problema, sin ejecutar nada."""
    data = {name: load_set(name, directory) for name in SET_NAMES}
    labels = {c["label"] for c in data["evaluation"]}
    missing = [v for v in VERDICTS if v not in labels]
    if missing:
        raise DatasetError(f"evaluation: faltan casos etiquetados como {missing}")
    return data
