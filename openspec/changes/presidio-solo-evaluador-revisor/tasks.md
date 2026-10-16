# Tasks

## 1. Configuracion de LiteLLM

- [x] 1.1 En `infra/litellm/config.yaml`, cambiar `presidio-pii` de `default_on: true` a `default_on: false` (manteniendo `mode: "pre_call"`, `presidio_filter_scope: "input"` y `pii_entities_config`).
- [x] 1.2 En `model_list`, anadir `guardrails: ["presidio-pii"]` a los deployments `evaluator` y `reviewer`. Verificar que el YAML sigue valido.
- [x] 1.3 Comprobar que `lakera-guard` sigue en `default_on: true` y sin cambios.

## 2. Despliegue

- [x] 2.1 Recrear `litellm` (`docker compose up -d --force-recreate litellm`) y confirmar en los logs que arranca sin error con los dos guardrails cargados.

## 3. Verificacion

- [x] 3.1 Evaluador: confirmar que la llamada del `evaluator` lleva el guardrail `presidio-pii` y que el dato aparece enmascarado para el proveedor. Verificado por sonda directa al proxy: cabecera `x-litellm-applied-guardrails: presidio-pii` y el modelo percibe `IP <IP_ADDRESS>`, `tarjeta <CREDIT_CARD>`, `email <EMAIL_ADDRESS>`.
- [x] 3.2 Revisor: misma comprobacion sobre una llamada del `reviewer`. Verificado: `x-litellm-applied-guardrails: presidio-pii` y datos enmascarados.
- [x] 3.3 Agente web, de codigo y de ejercicios: confirmar que sus llamadas **no** llevan `presidio-pii` y que el input llega sin marcadores. Verificado: `generator` -> `x-litellm-applied-guardrails: lakera-guard` (sin presidio) y el modelo percibe el email/IP/tarjeta tal cual.
- [x] 3.4 Repetir una generacion completa de ejercicios sobre un repo y confirmar que llega a `ready` (el contenido generado no lleva `<PERSON>`/`<EMAIL_ADDRESS>`/etc. incrustado). Verificado por el usuario.
- [x] 3.5 Confirmar que `lakera-guard` sigue activo en las llamadas de los 5 agentes. Verificado: `default_on: true` sin cambios y `x-litellm-applied-guardrails: lakera-guard` en `generator` (logs: "Monitoring mode - violation detected but allowing request").
- [x] 3.6 `openspec validate --all`: 0 fallos. Verificado (25 passed, 0 failed).

## 4. Spec

- [ ] 4.1 Confirmar que `openspec/specs/pii-redaction/spec.md` describe el alcance como evaluador/revisor (el delta se sincroniza al archivar el change).
