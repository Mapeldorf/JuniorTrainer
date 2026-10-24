# Tasks

## 1. Lectura y validacion del importe por entorno

- [x] 1.1 En `infra/litellm/provision_keys.py`, sustituir la constante `_MAX_BUDGET_USD = 5` por `_DEFAULT_MAX_BUDGET_USD = 5.0` y `_MAX_BUDGET_ENV_VAR = "LITELLM_KEY_MAX_BUDGET_USD"`, y añadir `_read_max_budget()` que devuelve el valor de la variable (o el defecto) validado como numero > 0, levantando `ValueError` con un mensaje que nombra la variable si no lo es.
- [x] 1.2 En `main()`, leer el budget con `_read_max_budget()` dentro de un `try/except ValueError` que imprime `Error: ...` y devuelve 1, junto a la comprobacion de `LITELLM_MASTER_KEY`, antes de abrir el cliente HTTP.
- [x] 1.3 Pasar el `max_budget` validado como parametro a `_generate_key` y `_missing_fields` (en vez de leer una constante global), conservando que `_missing_fields` solo lo escribe cuando `existing["max_budget"] is None`.
- [x] 1.4 Actualizar la cabecera/docstring del script y el comentario del budget para documentar la variable `LITELLM_KEY_MAX_BUDGET_USD` (5 por defecto en desarrollo, 50 en produccion) y la invariante de que no se sobrescribe un budget ya puesto.

## 2. Test sin red del arnes de aprovisionamiento

- [x] 2.1 Añadir `infra/litellm/test_provision_keys.py` (biblioteca estandar `unittest`) que cubra: `_read_max_budget()` sin variable devuelve 5.0; con `LITELLM_KEY_MAX_BUDGET_USD=50` devuelve 50.0; con un valor no numerico o <= 0 levanta `ValueError`; `_missing_fields` escribe `max_budget` con el valor pasado cuando falta y no lo incluye cuando la key ya tiene uno distinto.
- [x] 2.2 Ejecutar `python infra/litellm/test_provision_keys.py` y verificar que pasa (8 tests OK). Verificado tambien que `python -c "import ast; ast.parse(open('infra/litellm/provision_keys.py').read())"` no falla.

## 3. Verificacion contra el stack real (requiere el proxy del usuario)

- [ ] 3.1 Con el proxy LiteLLM levantado, borrar una key de prueba (`/key/delete`) y re-ejecutar `LITELLM_MASTER_KEY=... python infra/litellm/provision_keys.py` sin la variable; verificar con `/key/list?key_alias=<alias>&return_full_object=true` que la key nueva tiene `max_budget=5.0`.
- [ ] 3.2 Borrar de nuevo esa key y re-ejecutar con `LITELLM_KEY_MAX_BUDGET_USD=50`; verificar que la key nueva tiene `max_budget=50.0`.
- [ ] 3.3 Re-ejecutar el script sobre las keys ya existentes con un valor distinto al que tienen y verificar que se reportan como "ya existe completa, omitida" (no se sobrescribe el budget).
