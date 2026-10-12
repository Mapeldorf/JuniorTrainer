"""Verificacion de la tarea 4.2: sandboxing de list_files/read_file.

A diferencia de los demas scripts de verificacion de este change, este no
depende de ningun servicio externo (Postgres, LiteLLM, Langfuse): list_files
y read_file son pura logica de filesystem, asi que se puede ejecutar y
verificar sin salir de este entorno.

Crea un repo de prueba en un directorio temporal con:
  - un fichero normal (src/main.py)
  - un directorio ignorado (node_modules/) que list_files SHALL saltar
  - .git/ (tambien ignorado)
  - un fichero FUERA del repo, para probar los dos vectores de escape:
    "../" y una ruta absoluta.

Uso:
    python -m scripts.verify_filesystem_sandbox
"""

import tempfile
from pathlib import Path

from app.tools.filesystem import FileBudget, FileBudgetExceeded, PathEscapesRepo, list_files, read_file


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("print('hola')\n")
        (root / "node_modules").mkdir()
        (root / "node_modules" / "junk.js").write_text("ignorame")
        (root / ".git").mkdir()
        (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        (root / "README.md").write_text("# demo\n")
        outside = Path(tmp).parent / "secreto_fuera.txt"
        outside.write_text("no deberias poder leer esto\n")

        entries = list_files(str(root))
        paths = [e.path for e in entries]
        print(f"list_files: {paths}")
        assert "src/main.py" in paths
        assert "README.md" in paths
        assert not any("node_modules" in p for p in paths), "node_modules no deberia aparecer"
        assert not any(p.startswith(".git") for p in paths), ".git no deberia aparecer"

        budget = FileBudget(max_calls=2)
        content = read_file(str(root), "src/main.py", budget)
        assert content == "print('hola')\n"
        assert budget.used == 1
        print(f"read_file ok, budget.used={budget.used}")

        try:
            read_file(str(root), "../secreto_fuera.txt", budget)
            raise AssertionError("deberia haber rechazado ../secreto_fuera.txt")
        except PathEscapesRepo as e:
            print(f"OK, rechazado (../): {e}")
        assert budget.used == 1, "un intento rechazado no deberia consumir budget"

        try:
            read_file(str(root), str(outside), budget)
            raise AssertionError("deberia haber rechazado una ruta absoluta")
        except PathEscapesRepo as e:
            print(f"OK, rechazado (absoluta): {e}")
        assert budget.used == 1

        read_file(str(root), "README.md", budget)
        assert budget.used == 2
        try:
            read_file(str(root), "README.md", budget)
            raise AssertionError("deberia haber agotado el budget")
        except FileBudgetExceeded as e:
            print(f"OK, budget agotado: {e}")

    print("OK: list_files/read_file sandboxing + budget funcionan como se espera")


if __name__ == "__main__":
    main()
