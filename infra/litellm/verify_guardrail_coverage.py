"""Comprobacion estatica de la cobertura de guardarrailes del proxy LiteLLM.

Requisitos "Cobertura de guardarrailes en los deployments de fallback" y
"Verificacion estatica de la cobertura de guardarrailes" de
`specs/agent-resilience/spec.md` (change `guardarrailes-por-capas`).

Por que existe. Los guardarrailes de LiteLLM se resuelven **por deployment**,
y un deployment de fallback es una entrada distinta de la de su primario. Es
decir, vincular un guardarrail a `evaluator` no lo vincula a
`evaluator-fallback-hf`: hay que acordarse de hacerlo en los dos. Olvidarlo no
rompe nada visible, porque el fallback solo entra en juego cuando el proveedor
principal falla -- justo el momento en el que nadie esta mirando. Esta
comprobacion convierte ese "hay que acordarse" en una invariante verificada.

Las dos invariantes:

  1. **Cobertura del fallback.** Todo deployment de fallback lleva vinculados
     al menos los mismos guardarrailes explicitos que su deployment primario,
     recorriendo `litellm_settings.fallbacks`.
  2. **Red de seguridad de redaccion.** Existe al menos un guardarrail de
     redaccion de PII con `default_on: true` y con todas sus entidades en
     modo de sustitucion por marcador (`MASK`), de modo que cualquier
     deployment -- incluido uno que se anada en el futuro sin vincularle nada
     -- nazca con redaccion de PII.

Solo se comparan los guardarrailes **explicitos** (los de
`model_list[].litellm_params.guardrails`). Los globales (`default_on: true`)
se aplican a todo por definicion, asi que no tiene sentido exigirlos en la
lista de un deployment concreto; la invariante 2 es la que garantiza que
existan.

No necesita red, ni modelo, ni credenciales, ni el stack levantado: solo lee
un fichero YAML. Por eso puede ejecutarse en integracion continua en cada
cambio, a diferencia de las comprobaciones `verify_*.py` de los agentes.

Uso:
    python infra/litellm/verify_guardrail_coverage.py              # configuracion real
    python infra/litellm/verify_guardrail_coverage.py --self-test  # casos sinteticos

Codigos de salida: 0 si la configuracion cumple las invariantes, 1 si no.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_DEFAULT_CONFIG = Path(__file__).resolve().parent / "config.yaml"


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"{path} no contiene un objeto YAML en la raiz")
    return config


def explicit_guardrails(config: dict) -> dict[str, set[str]]:
    """Guardarrailes vinculados explicitamente a cada `model_name`.

    Un `model_name` puede aparecer en varias entradas de `model_list` (varios
    deployments detras del mismo alias logico); en ese caso se toma la union,
    que es lo conservador: si alguno de ellos declara un guardarrail, el
    fallback de ese alias tiene que cubrirlo.
    """
    result: dict[str, set[str]] = {}
    for entry in config.get("model_list") or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("model_name")
        if not name:
            continue
        params = entry.get("litellm_params") or {}
        guardrails = params.get("guardrails") or []
        result.setdefault(name, set()).update(guardrails)
    return result


def fallback_pairs(config: dict) -> list[tuple[str, str]]:
    """Pares (primario, fallback) declarados en `litellm_settings.fallbacks`."""
    pairs: list[tuple[str, str]] = []
    settings = config.get("litellm_settings") or {}
    for item in settings.get("fallbacks") or []:
        if not isinstance(item, dict):
            continue
        for primary, fallbacks in item.items():
            for fallback in fallbacks or []:
                pairs.append((primary, fallback))
    return pairs


def check_fallback_coverage(config: dict) -> list[str]:
    """Invariante 1: todo fallback cubre los guardarrailes de su primario."""
    guardrails = explicit_guardrails(config)
    known = set(guardrails)
    problems: list[str] = []

    for primary, fallback in fallback_pairs(config):
        if primary not in known:
            problems.append(
                f"el fallback declara como primario '{primary}', que no existe en model_list"
            )
            continue
        if fallback not in known:
            problems.append(
                f"'{primary}' declara el fallback '{fallback}', que no existe en model_list"
            )
            continue
        missing = guardrails[primary] - guardrails[fallback]
        if missing:
            problems.append(
                f"el deployment de fallback '{fallback}' no lleva "
                f"{sorted(missing)}, que su primario '{primary}' si lleva: una "
                "llamada desviada al proveedor de respaldo perderia esa proteccion"
            )
    return problems


def check_global_redaction(config: dict) -> list[str]:
    """Invariante 2: existe una redaccion de PII global en modo MASK."""
    for entry in config.get("guardrails") or []:
        if not isinstance(entry, dict):
            continue
        params = entry.get("litellm_params") or {}
        if params.get("guardrail") != "presidio":
            continue
        if params.get("default_on") is not True:
            continue
        entities = params.get("pii_entities_config") or {}
        if entities and all(action == "MASK" for action in entities.values()):
            return []

    return [
        "no hay ningun guardarrail de redaccion de PII con default_on: true y "
        "todas sus entidades en MASK: un deployment nuevo naceria sin red de "
        "seguridad de redaccion"
    ]


def check(config: dict) -> list[str]:
    return check_fallback_coverage(config) + check_global_redaction(config)


_SELF_TEST_CASES: list[tuple[str, dict, int]] = [
    (
        "configuracion coherente",
        {
            "model_list": [
                {"model_name": "evaluator", "litellm_params": {"guardrails": ["lakera-block"]}},
                {
                    "model_name": "evaluator-fallback-hf",
                    "litellm_params": {"guardrails": ["lakera-block"]},
                },
            ],
            "litellm_settings": {"fallbacks": [{"evaluator": ["evaluator-fallback-hf"]}]},
            "guardrails": [
                {
                    "guardrail_name": "presidio-pii",
                    "litellm_params": {
                        "guardrail": "presidio",
                        "default_on": True,
                        "pii_entities_config": {"EMAIL_ADDRESS": "MASK"},
                    },
                }
            ],
        },
        0,
    ),
    (
        "fallback descubierto",
        {
            "model_list": [
                {"model_name": "evaluator", "litellm_params": {"guardrails": ["lakera-block"]}},
                {"model_name": "evaluator-fallback-hf", "litellm_params": {}},
            ],
            "litellm_settings": {"fallbacks": [{"evaluator": ["evaluator-fallback-hf"]}]},
            "guardrails": [
                {
                    "guardrail_name": "presidio-pii",
                    "litellm_params": {
                        "guardrail": "presidio",
                        "default_on": True,
                        "pii_entities_config": {"EMAIL_ADDRESS": "MASK"},
                    },
                }
            ],
        },
        1,
    ),
    (
        "sin red global de redaccion",
        {
            "model_list": [{"model_name": "evaluator", "litellm_params": {}}],
            "litellm_settings": {"fallbacks": []},
            "guardrails": [
                {
                    "guardrail_name": "presidio-pii",
                    "litellm_params": {
                        "guardrail": "presidio",
                        "default_on": False,
                        "pii_entities_config": {"EMAIL_ADDRESS": "MASK"},
                    },
                }
            ],
        },
        1,
    ),
    (
        "red global en BLOCK no sirve como red de redaccion",
        {
            "model_list": [{"model_name": "evaluator", "litellm_params": {}}],
            "litellm_settings": {"fallbacks": []},
            "guardrails": [
                {
                    "guardrail_name": "presidio-pii-block",
                    "litellm_params": {
                        "guardrail": "presidio",
                        "default_on": True,
                        "pii_entities_config": {"EMAIL_ADDRESS": "BLOCK"},
                    },
                }
            ],
        },
        1,
    ),
]


def self_test() -> int:
    failures = 0
    for name, config, expected in _SELF_TEST_CASES:
        problems = check(config)
        got = 1 if problems else 0
        if got != expected:
            failures += 1
            print(f"FALLO  {name}: se esperaban {expected} problemas, se obtuvo {problems}")
        else:
            print(f"OK     {name}")
    if failures:
        print(f"\n{failures} caso(s) sinteticos no se comportan como se espera.")
        return 1
    print(f"\nLos {len(_SELF_TEST_CASES)} casos sinteticos se comportan como se espera.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="comprueba la propia logica con configuraciones sinteticas",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        help="ruta del config.yaml del proxy (por defecto, el del repositorio)",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    try:
        config = load_config(args.config)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"no se pudo leer {args.config}: {exc}", file=sys.stderr)
        return 1

    problems = check(config)
    if problems:
        print(f"La cobertura de guardarrailes de {args.config} es incorrecta:\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"Cobertura de guardarrailes correcta en {args.config}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
