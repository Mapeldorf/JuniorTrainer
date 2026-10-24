"""Refresca `evals/prices.json` desde la lista publica de modelos de OpenRouter.

    python -m evals.update_prices

Solo lee (sin credenciales) y solo actualiza los modelos que ya figuran en la
tabla. Los planes de Tavily no se refrescan aqui: se anotan a mano con su fuente.
"""

import sys

from evals import prices


def main() -> int:
    try:
        changes = prices.refresh()
    except OSError as exc:
        print(f"no se pudo consultar la lista de modelos: {exc}", file=sys.stderr)
        return 2
    if not changes:
        print("precios sin cambios (se actualiza solo la fecha)")
    for model_id, (old, new) in changes.items():
        print(f"{model_id}: {old} -> {new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
