# Proposal

## Why

En `agents/code/app/service.py`, `_pick_files` le pide al modelo que elija hasta 10 rutas de fichero a partir del listado real del repositorio, y `analyze_repo` pasa esas rutas (`chosen_paths`) tal cual a `read_file(owner, repo, commit_sha, path, budget)` (`agents/code/app/tools/github_repo.py`), que las interpola sin validar en la URL de la Contents API de GitHub (`f"/repos/{owner}/{repo}/contents/{path}"`). A diferencia de `owner`/`repo` (que ya se validan contra una expresion estricta antes de construir ninguna URL, requisito "Referencia de entrada del repositorio" de `specs/github-repo-access/spec.md`), `path` solo se comprueba que sea `str` (`_pick_files`, linea 158): ninguna validacion impide que sea `../../algo`, una ruta absoluta, o cualquier otro valor que el modelo devuelva.

El contenido de los ficheros del propio repositorio ya llega al prompt del modelo marcado explicitamente como dato, no como instruccion (requisito "Contenido del repositorio tratado como datos, no como instrucciones"), precisamente porque un repositorio de un tercero puede intentar manipular al modelo. Esa mitigacion cubre el contenido de los ficheros, pero no evita que un modelo manipulado (o que simplemente alucine) devuelva una `path` fuera de la lista real de ficheros del repositorio, y hoy nada lo detectaria antes de llamar a la API de GitHub con ella.

Investigacion relacionada (conversacion previa): `owner`/`repo` SSRF/inyeccion ya esta cubierto por el requisito existente y no necesita cambios; este es un hallazgo distinto en el mismo area.

## What Changes

- `read_file` (o su llamador `analyze_repo`) deja de aceptar cualquier `path` devuelto por el modelo: solo se leen rutas que esten literalmente presentes en el listado real obtenido por `list_files` para ese `commit_sha` (cross-check contra una fuente de verdad, no solo un patron de caracteres permitidos -- las rutas de fichero legitimas pueden variar mucho mas que `owner`/`repo`, asi que una regex generica no serviria igual de bien que comprobar pertenencia al conjunto ya conocido).
- Una `path` elegida por el modelo que no este en el listado real se descarta (se trata igual que hoy se trata un `FileNotFoundError`/`GitHubRepoError`: se loguea y se salta ese fichero, sin fallar la tarea entera), en vez de intentar leerla contra la API de GitHub.

## Capabilities

### New Capabilities
(ninguna)

### Modified Capabilities
- `github-repo-access`: nuevo requisito sobre que rutas de fichero puede leer el agente de codigo dentro de un repositorio ya autorizado.

## Impact

- `agents/code/app/service.py`: `analyze_repo`/`_pick_files` (o una funcion nueva de filtrado entre ambas).
- `agents/code/app/tools/github_repo.py`: sin cambios en `read_file` en si (su contrato no cambia), si el filtrado se hace en `service.py` antes de llamarla.
- Sin cambios en `backend/app` (este hallazgo es especifico del agente de codigo, no del backend que ya valida `owner`/`repo`).
