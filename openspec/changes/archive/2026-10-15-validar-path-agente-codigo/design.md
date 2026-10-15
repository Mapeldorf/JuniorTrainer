# Design

## Context

`analyze_repo` (`agents/code/app/service.py`) ya tiene en memoria `entries: list[FileEntry]` (el listado real del repositorio, obtenido de `list_files`) en el momento en que recibe `chosen_paths` del modelo. No hace falta ninguna llamada ni dato nuevo: la fuente de verdad para validar ya esta disponible en el mismo scope. Ver `proposal.md` para el hallazgo.

## Goals / Non-Goals

**Goals:**
- Que ninguna llamada a `read_file` use una `path` que no provenga literalmente del listado real del repositorio para ese commit.
- Que una ruta descartada se trate igual que hoy se trata un fichero no encontrado (se loguea y se continua), sin cambiar el contrato de `analyze_repo` ni fallar la tarea completa por una sola ruta mala.

**Non-Goals:**
- No se valida `path` con una expresion regular de caracteres permitidos (tipo la de `owner`/`repo`): las rutas de fichero legitimas pueden tener casi cualquier caracter (espacios, puntos, mayusculas, subcarpetas con nombres arbitrarios), asi que una regex razonable para repos reales seria o muy permisiva (no protegeria nada) o rompería casos legitimos. El cross-check contra el listado real es mas simple y estrictamente mas seguro: solo pueden leerse rutas que de verdad existen en el repositorio.
- No se cambia `read_file` en `tools/github_repo.py`: su contrato (leer lo que se le pida) no cambia; el filtrado vive en `service.py`, que es quien conoce el listado real y quien ya decide que rutas intentar leer.

## Decisions

- **Filtrar `chosen_paths` contra `{e.path for e in entries}` antes del bucle de lectura en `analyze_repo`.** Construir el `set` de paths validos una vez (no en cada iteracion) y comprobar pertenencia; las rutas que no esten se tratan como hoy se tratan los `GitHubRepoError`/`FileNotFoundError` (log + `continue`), sin necesidad de un nuevo tipo de excepcion.
- **El filtrado ocurre antes de descontar budget.** Una ruta que ya se sabe invalida (no esta en el listado) no debe consumir una de las 10 lecturas del `FileBudget`: el budget protege contra gastar llamadas reales a la API, y rechazar una ruta inventada no hace ninguna llamada.

## Risks / Trade-offs

- [El modelo podria elegir una variante de una ruta real con una diferencia trivial (mayusculas/minusculas, barra inicial) que el cross-check exacto rechace aunque "deberia" referirse al mismo fichero] -> Mitigacion: es preferible descartar ese caso (se trata igual que una alucinacion del modelo, el sistema ya tolera perder algunos de los 10 ficheros elegidos) a normalizar/adivinar la intencion, que reintroduciria la superficie de ambigüedad que este cambio quiere cerrar.
