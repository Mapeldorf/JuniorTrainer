# Tasks

## 1. Extender el script de aprovisionamiento

- [x] 1.1 En `infra/litellm/provision_keys.py`, añadir la constante `_RPM_LIMIT = 60`. Incluir `rpm_limit` en el body de `POST /key/generate` (`_generate_key`) junto a `max_budget`/`budget_duration`.
- [x] 1.2 Extender la logica de upsert (`main()`/`_apply_budget` o equivalente) para que, al encontrar una key existente sin `rpm_limit`, la actualice via `POST /key/update` junto con el budget si tambien le faltara (una sola llamada de update cuando falten varios campos, no una por campo). Si la key ya tiene `rpm_limit` puesto (aunque le faltara el budget u otro campo), no tocar ese campo al actualizar los demas. Implementado con `_missing_fields()` (construye el dict solo con lo que falta) + `_apply_missing_fields()` (una unica llamada a `/key/update` con ese dict).
- [x] 1.3 Verificar que `python -c "import ast; ast.parse(open('infra/litellm/provision_keys.py').read())"` no falla. Verificado.

## 2. Aplicar el limite a las 5 keys existentes

- [x] 2.1 Ejecutar el script sobre las 5 keys ya existentes en el `.env` local y verificar con `GET /key/list?key_alias=<alias>&return_full_object=true` que las 5 quedan con `rpm_limit: 60`. Verificado: las 5 se actualizaron solo con `rpm_limit` (ya tenian budget, confirma que el upsert por campo no toca lo que ya estaba puesto).
- [x] 2.2 Re-ejecutar el script inmediatamente despues y confirmar que no vuelve a tocar esas 5 keys (ya tienen `rpm_limit` puesto). Verificado: las 5 reportan "ya existe completa, omitida".

## 3. Verificacion end-to-end del limite

- [x] 3.1 Con una de las 5 keys, enviar mas de 60 peticiones en menos de un minuto (p. ej. un bucle de `curl` a `/chat/completions`) y confirmar que, pasado el limite, LiteLLM empieza a rechazar con `429` sin invocar al proveedor (verificar que no hay coste/latencia de proveedor en las peticiones rechazadas). Verificado con `agent-code`: 65 peticiones en 32s, las primeras 60 responden `200`, de la 61 en adelante `429` con `"type":"throttling_error"`, `"Current limit: 60"` -- rechazo instantaneo, sin invocar al proveedor.
- [x] 3.2 Confirmar que las otras 4 keys siguen funcionando con normalidad mientras la primera esta rechazando por rate limit (el limite es por key, no global). Verificado: las 4 restantes responden `200` mientras `agent-code` sigue en `429`.
- [x] 3.3 Esperar a que pase la ventana de un minuto y confirmar que la key vuelve a aceptar peticiones con normalidad. Verificado: tras el reset indicado en el propio error (`Limit resets at`), la misma key vuelve a responder `200` con normalidad.
