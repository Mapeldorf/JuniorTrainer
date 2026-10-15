# Tasks

## 1. Configuracion del guardrail

- [ ] 1.1 En `infra/litellm/config.yaml`, quitar `URL` y `PERSON` de `pii_entities_config` del guardrail `presidio-pii`, dejando `EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `IP_ADDRESS`, `IBAN_CODE`. Verificar que el YAML sigue valido.
- [ ] 1.2 En el mismo guardrail, añadir `presidio_filter_scope: "input"` para que la redaccion no se aplique al output del modelo.
- [ ] 1.3 Recrear `litellm` (`docker compose up -d --force-recreate litellm`) y confirmar en los logs que arranca sin error con el guardrail cargado.

## 2. Verificacion

- [ ] 2.1 Con una virtual key real, repetir una generacion sobre un repo Angular con tecnologia "Servicios en Angular" y confirmar que el agente de codigo lee ficheros reales (no devuelve `no se pudo leer ningun fichero de los elegidos por el modelo`). En la traza de Langfuse, el listado de rutas del input de `litellm:agent-code` debe llegar sin `<URL>`/`<PERSON>`.
- [ ] 2.2 Confirmar que un email y un telefono inventados en el input siguen apareciendo enmascarados para el proveedor (la redaccion de PII de riesgo real sigue activa).
- [ ] 2.3 Confirmar que el contenido generado (campos del ejercicio) ya no sale con marcadores incrustados (`<PERSON>`, `<EMAIL_ADDRESS>`, etc.): en los spans `guardrail` de `presidio-pii` con `guardrail_mode: ["post_call"]` no debe haber entidades enmascaradas.
- [ ] 2.4 Confirmar que `openspec/specs/pii-redaction/spec.md` ya no menciona URL ni nombre de persona y recoge el requisito de que el output no se redacta.
