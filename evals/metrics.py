"""Metricas puras de la suite de evaluacion: sin E/S ni dependencias.

Cada funcion recibe datos ya extraidos de los resultados y devuelve un numero
(o `None` cuando la metrica no esta disponible porque no hay casos: una
metrica sin casos no es cero, ver spec `agent-evaluation`).
"""

import math
import re
import unicodedata

VERDICTS = ("correct", "incomplete", "incorrect")


def rate(numerator: int, denominator: int) -> float | None:
    """Proporcion `numerator/denominator`, o `None` si no hay casos."""
    if denominator == 0:
        return None
    return numerator / denominator


def accuracy(pairs: list[tuple[str, str]]) -> float | None:
    """Exactitud sobre pares `(esperado, obtenido)`."""
    return rate(sum(1 for expected, got in pairs if expected == got), len(pairs))


def confusion_matrix(
    pairs: list[tuple[str, str]], labels: tuple[str, ...] = VERDICTS
) -> dict[str, dict[str, int]]:
    """Matriz `matriz[esperado][obtenido]` con todas las etiquetas presentes
    aunque su recuento sea cero."""
    matrix = {e: {g: 0 for g in labels} for e in labels}
    for expected, got in pairs:
        if expected in matrix and got in matrix[expected]:
            matrix[expected][got] += 1
    return matrix


def cohen_kappa(pairs: list[tuple[str, str]], labels: tuple[str, ...] = VERDICTS) -> float | None:
    """Kappa de Cohen entre la etiqueta esperada y la obtenida.

    `None` sin casos. Si la concordancia esperada por azar es 1 (una unica
    etiqueta en ambas series) el kappa no esta definido: se devuelve 1.0 si
    coinciden todos los casos y `None` en otro caso.
    """
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(1 for e, g in pairs if e == g) / n
    expected_by_chance = sum(
        (sum(1 for e, _ in pairs if e == label) / n) * (sum(1 for _, g in pairs if g == label) / n)
        for label in labels
    )
    if math.isclose(expected_by_chance, 1.0):
        return 1.0 if math.isclose(observed, 1.0) else None
    return (observed - expected_by_chance) / (1 - expected_by_chance)


def percentile(values: list[float], pct: float) -> float | None:
    """Percentil por el metodo del rango mas cercano (determinista, sin
    interpolar): el valor en la posicion `ceil(pct/100 * n)` de la serie
    ordenada."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


def latency_summary(durations_ms: list[float]) -> dict[str, float | None]:
    return {
        "p50_ms": percentile(durations_ms, 50),
        "p95_ms": percentile(durations_ms, 95),
        "p99_ms": percentile(durations_ms, 99),
    }


def word_count(text: str) -> int:
    return len(text.split())


_TERM_RE = re.compile(r"[a-z0-9_]+")

# Palabras vacias frecuentes en los enunciados; sin ellas el solapamiento
# mide el tema y no la gramatica compartida.
_STOPWORDS = frozenset(
    "a al algo ante como con cual cuando de del desde donde el ella en es esta este "
    "ese esto ha hace hacer la las le les lo los mas me mi no o para pero por que "
    "que se segun ser si sin sobre su sus tu un una uno unos unas y ya".split()
)


def terms(text: str) -> frozenset[str]:
    """Terminos significativos de un texto: minusculas, sin tildes ni
    palabras vacias ni terminos de un solo caracter."""
    folded = unicodedata.normalize("NFKD", text.lower())
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return frozenset(t for t in _TERM_RE.findall(folded) if len(t) > 1 and t not in _STOPWORDS)


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    """Indice de Jaccard entre dos conjuntos de terminos. Dos conjuntos
    vacios se consideran identicos (1.0)."""
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def max_overlap(new_statements: list[str], previous_statements: list[str]) -> float | None:
    """Mayor solapamiento de Jaccard entre algun enunciado nuevo y alguno
    previo; `None` si no hay nada con que comparar."""
    if not new_statements or not previous_statements:
        return None
    previous_terms = [terms(s) for s in previous_statements]
    return max(jaccard(terms(n), p) for n in new_statements for p in previous_terms)


def precision_recall(
    predicted: set[str], expected: set[str]
) -> tuple[float | None, float | None]:
    """Precision y cobertura de un conjunto predicho frente a uno esperado."""
    true_positives = len(predicted & expected)
    return rate(true_positives, len(predicted)), rate(true_positives, len(expected))
