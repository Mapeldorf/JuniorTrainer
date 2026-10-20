# Tasks

## 1. Agente validador: contexto de la llamada

- [x] 1.1 Añadir el parseo del campo `context` del mensaje A2A en `agents/validator/app/input.py` (hermano de `technologies`, mismo origen de datos que `parse_technologies`), normalizado a `"catalog_entry"` o `"generation"` con `"catalog_entry"` como valor por defecto ante ausencia o valor no reconocido. Verificar con un test unitario que cubre: `context="generation"`, `context="catalog_entry"`, sin `context`, y un valor desconocido (los tres ultimos devuelven `"catalog_entry"`).
- [x] 1.2 Cambiar `validate_technologies` (`agents/validator/app/service.py`) para aceptar el contexto parseado en 1.1 y, cuando sea `"generation"`, omitir por completo la llamada a `list_catalog_technologies()` y la seccion de duplicados del prompt y de `_RESPONSE_FORMAT` (sin pedir `duplicate_technologies` al modelo). Verificar con un test unitario que mockea `list_catalog_technologies` y comprueba que no se llama en contexto `"generation"`, y que si se llama en contexto `"catalog_entry"` (comportamiento sin cambios).
- [x] 1.3 Confirmar que `_parse_result` sigue aceptando una respuesta sin `duplicate_technologies` cuando el contexto es `"generation"` (esquema simplificado) y que `ValidationResult.duplicate_technologies` queda `[]` en ese caso, sin romper la coherencia defensiva ya existente para el caso `"catalog_entry"`. Verificar con un test unitario por cada contexto.
- [x] 1.4 Pasar el contexto desde `agents/validator/app/executor.py` hasta `validate_technologies`. Verificar leyendo el flujo completo mensaje A2A → `parse_technologies`/parseo de `context` → `validate_technologies`.

## 2. Backend: indicar el contexto en cada llamador

- [x] 2.1 En `backend/app/routers/technologies.py`, añadir `"context": "catalog_entry"` al payload que ya envia `send_a2a_task` al validador. Verificar con un test de integracion del endpoint que comprueba el payload enviado (mock de `send_a2a_task`) o, si no hay mock de payload, que el comportamiento de alta (409/422/201) sigue igual que antes del cambio.
- [x] 2.2 En `backend/app/orchestrator.py` (`_call_validator`), añadir `"context": "generation"` al payload. Verificar con un test de integracion/unitario de `_call_validator` que comprueba el payload enviado.

## 3. Verificacion end-to-end del caso que fallaba

- [x] 3.1 Ampliar `agents/validator/scripts/verify_validator.py` con un caso que llama a `validate_technologies(["<tecnologia ya existente en el catalogo de desarrollo>"], context="generation")` y comprueba `valid=True` (no se rechaza por duplicado de si misma), y otro caso que llama a la misma tecnologia con `context="catalog_entry"` y comprueba que sigue siendo tratada como duplicado (`valid=False`, `duplicate_technologies` no vacio) -- mismo comportamiento que antes del cambio para ese contexto. Verificar ejecutando `python -m scripts.verify_validator` contra LiteLLM y la base de datos de desarrollo.
- [x] 3.2 Reproducir manualmente el caso original que motivo este cambio: iniciar una generacion con una tecnologia ya existente en el catalogo (p. ej. "RxJS en Angular") y comprobar que ya no falla en el paso de validacion. Verificar con el flujo real (`POST /generations` + `GET /generations/{id}`) contra el entorno docker-compose local, hasta ver que la generacion avanza mas alla de la validacion.

## 4. Documentacion y specs

- [x] 4.1 Actualizar el comentario de modulo de `agents/validator/app/service.py` (la cabecera que describe la comprobacion de duplicados) para mencionar que ahora depende del contexto de la llamada. Verificar leyendo el fichero actualizado.
- [x] 4.2 Revisar `docs/especificacion-agentes.md` y `docs/especificacion-backend.md` y actualizar la descripcion del validador si describen el comportamiento de duplicados sin distincion de contexto. Verificar leyendo los ficheros actualizados.
- [x] 4.3 Ejecutar `openspec validate validador-contexto-generacion --strict` y corregir cualquier aviso antes de dar la propuesta por lista para implementar.

## Workflow follow-up

- Archivar el change y sincronizar `openspec/specs/technology-validation/spec.md` una vez implementado y revisado.
