"""Verificacion manual de search_saved_exercises: solo devuelve ejercicios
guardados (`saved = true`) o eliminados (`deleted_at` no nulo), nunca uno
que no sea ninguno de los dos.

Change `eliminar-memoria-agente-ejercicios`: antes (tarea 5.2) solo
devolvia guardados; ahora tambien devuelve eliminados, al ser la unica
fuente de "enunciados a evitar" del agente de ejercicios (ver design.md).

Uso (desde agents/exercises/, con AGENTS_PG_HOST/AGENTS_PG_PORT/
AGENTS_PG_DATABASE, SUPABASE_PROJECT_REF y AGENTS_EXERCISE_READER_PASSWORD
en el .env de la raiz del repo apuntando a Supabase con la migracion
0003 aplicada, y al menos un ejercicio type='debug' guardado o eliminado
ya existente en public.exercise -- si la tabla esta vacia para ese tipo,
el script lo avisa pero no falla):
    python -m scripts.verify_saved_exercises <exercise_type>

Por ejemplo:
    python -m scripts.verify_saved_exercises debug
"""

import asyncio
import sys

from app.db import exercise_reader_conn_string
from app.tools.saved_exercises import SearchBudget, SearchBudgetExceeded, search_saved_exercises


async def main() -> None:
    exercise_type = sys.argv[1] if len(sys.argv) > 1 else "debug"

    budget = SearchBudget(max_calls=3)
    results = await search_saved_exercises(exercise_reader_conn_string(), exercise_type, budget, limit=10)

    print(f"consultas gastadas del budget: {budget.used}/{budget.max_calls}")
    print(f"ejercicios guardados o eliminados encontrados ({exercise_type}): {len(results)}")
    for r in results:
        print(f"  - {r.statement!r} ({len(r.code)} bloques de codigo)")

    if not results:
        print(
            "AVISO: no se encontro ningun ejercicio guardado ni eliminado de ese tipo -- "
            "no es un fallo del tool, pero no hay nada que verificar visualmente. "
            "Inserta uno de prueba en public.exercise (saved=true, o con deleted_at puesto) y reintenta."
        )

    assert len(results) <= 10, "no deberian ser mas de 10 resultados"
    assert budget.used == 1, "esta llamada deberia haber gastado exactamente 1 consulta del budget"

    # El budget se agota al cuarto intento (limite de 3 por tarea).
    for _ in range(2):
        await search_saved_exercises(exercise_reader_conn_string(), exercise_type, budget, limit=10)
    try:
        await search_saved_exercises(exercise_reader_conn_string(), exercise_type, budget, limit=10)
    except SearchBudgetExceeded:
        print("OK: la 4a consulta de la misma tarea se rechaza (budget de 3 agotado)")
    else:
        raise AssertionError("la 4a consulta deberia haber lanzado SearchBudgetExceeded")

    print()
    print(
        "OK: revisa a mano en Supabase que todo ejercicio de la lista de arriba "
        "tiene saved=true o deleted_at distinto de NULL (nunca ninguno de los dos)."
    )


if __name__ == "__main__":
    asyncio.run(main())
