# Design

## Context

Ver `proposal.md` - Why. Presidio corre hoy como guardrail global (`default_on: true`) en `infra/litellm/config.yaml`, asi que se aplica a las llamadas de los 5 agentes. Todos los agentes pasan por el mismo proxy; los modelos logicos son `generator` (web, codigo y ejercicios), `evaluator` (evaluador) y `reviewer` (revisor). Solo evaluador y revisor reciben la respuesta del alumno.

## Goals / Non-Goals

**Goals:**
- Que la redaccion de PII se aplique solo a las llamadas que llevan texto del alumno.
- Sin cambios en `agents/*` ni en las virtual keys; cambio de configuracion en LiteLLM.
- Mantener `lakera-guard` sin tocar (sigue en los 5 agentes, en modo monitor).

**Non-Goals:**
- No afinar umbrales ni listas de entidades (`presidio_score_thresholds`/`presidio_entities_deny_list`): son globales y bajarian el recall justo en evaluador/revisor.
- No tocar el codigo de los agentes ni anadir un flag por peticion (el opt-out por request esta bloqueado a proposito en LiteLLM: solo lo decide la config de admin).
- No cambiar las entidades ni el `presidio_filter_scope: "input"` ya decididos en `2026-10-15-quitar-url-person-presidio`.

## Decisions

**1. Vinculacion por modelo (`default_on: false` + `litellm_params.guardrails`), no opt-out por key.**

`presidio-pii` pasa a `default_on: false` y se declara en el `litellm_params.guardrails` de los deployments `evaluator` y `reviewer`:

```yaml
model_list:
  - model_name: evaluator
    litellm_params:
      model: os.environ/EVALUATOR_MODEL
      guardrails: ["presidio-pii"]
  - model_name: reviewer
    litellm_params:
      model: os.environ/REVIEWER_MODEL
      guardrails: ["presidio-pii"]
```

LiteLLM resuelve los guardrails a nivel de modelo en el pipeline previo a la llamada (`check_and_merge_model_level_guardrails`, `litellm/proxy/utils.py`), tomando la union de guardrails de los deployments del alias. Como `evaluator` y `reviewer` tienen alias propios distintos de `generator`, la vinculacion separa exactamente los agentes que queremos sin tocar las keys.

Alternativa descartada: opt-out por key (`metadata.opted_out_global_guardrails: ["presidio-pii"]` en `infra/litellm/provision_keys.py`). Funciona (lo lee `_get_admin_metadata` solo de metadata de admin), pero obliga a reabastecer keys y a gestionar el upsert de `metadata` en el script, y deja la intencion menos visible que un `guardrails:` junto al deployment. El campo `disable_global_guardrails` de la key tambien se descarta: desactivaria tambien Lakera en esos agentes, y aqui solo queremos excluir Presidio.

**2. La redaccion sigue siendo de input y con las mismas entidades.** No se toca `presidio_filter_scope: "input"` ni `pii_entities_config` (email, telefono, tarjeta, IP, IBAN). Este change solo cambia *a quien* se aplica.

**3. El output sigue sin redactarse** (requisito ya vigente). No aplica aqui, pero se mantiene: el `default_on: false` no reintroduce el enmascarado de salida.

## Risks / Trade-offs

- [PII presente en contenido de repo o snippets de terceros llegaria sin redactar al proveedor] → aceptado: no es el dato del alumno y ese contenido ya viaja al mismo proveedor por otras rutas. La redaccion del texto del alumno (evaluador/revisor) se conserva.
- [Si alguien cambia los alias de modelo, la vinculacion se rompe en silencio (guardrail deja de aplicarse)] → verificacion explicita en tasks: traza de Langfuse con span `presidio-pii` en evaluador/revisor y sin el en web/codigo/ejercicios.
- [Olvidar `default_on: false` dejaria Presidio corriendo en los 5 y el cambio no tendria efecto] → forma parte de la verificacion (si aparece en web/codigo/ejercicios, no se aplico).

## Migration Plan

Cambio de configuracion: recrear `litellm` (`docker compose up -d --force-recreate litellm`) para que relea `config.yaml`. Rollback: devolver `presidio-pii` a `default_on: true` y quitar los `guardrails:` de `evaluator`/`reviewer`, y recrear. Sin despliegue de agentes ni de keys.

## Open Questions

Ninguna.
