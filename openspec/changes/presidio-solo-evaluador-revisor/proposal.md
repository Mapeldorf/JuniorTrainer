# Proposal

## Why

Tras `2026-10-15-quitar-url-person-presidio`, Presidio (`presidio-pii`) sigue corriendo `pre_call` sobre el input de **los 5 agentes**. Pero solo dos agentes reciben texto escrito por una persona: el **evaluador** y el **revisor** (la respuesta del alumno). Los otros tres procesan datos que no son PII del alumno: el **agente web** (snippets de busqueda de terceros), el **agente de codigo** (codigo de un repo de terceros) y el **agente de ejercicios** (resumenes y fragmentos derivados). Enmascarar ahi no aporta privacidad y si genera falsos positivos sobre contenido que el modelo debe reproducir o analizar (el caso real: fragmentos o rutas con marcadores `<EMAIL_ADDRESS>`/`<IP_ADDRESS>` incrustados).

Acotar la redaccion a las llamadas que llevan texto del alumno elimina ese riesgo de raiz y deja de depender de afinar umbrales o listas de entidades (`presidio_score_thresholds`/`presidio_entities_deny_list`), que son globales y bajan el recall justo donde la redaccion importa.

## What Changes

- `infra/litellm/config.yaml`: el guardrail `presidio-pii` pasa de `default_on: true` a `default_on: false`, y se vincula explicitamente a los modelos `evaluator` y `reviewer` con `litellm_params.guardrails: ["presidio-pii"]` en sus deployments de `model_list`. No se toca `lakera-guard` (sigue `default_on: true` en los 5 agentes).
- La redaccion sigue siendo de input (`presidio_filter_scope: "input"`) y con las mismas entidades (email, telefono, tarjeta, IP, IBAN).
- `openspec/specs/pii-redaction/spec.md`: el requisito de alcance pasa de "los 5 agentes" a "las llamadas que llevan texto del alumno (evaluador y revisor)"; se añade que las llamadas de web, codigo y ejercicios NO se redactan.
- Sin cambios en `agents/*`: el agente no pide guardrails; la vinculacion es por modelo en el proxy.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `pii-redaction`: el alcance de la redaccion deja de ser "toda llamada de los 5 agentes" y pasa a ser "las llamadas que llevan texto del alumno (evaluador y revisor)".

## Impact

- `infra/litellm/config.yaml`: `presidio-pii` (`default_on: false`) + `guardrails` en los deployments `evaluator` y `reviewer`.
- `openspec/specs/pii-redaction/spec.md`: requisitos de alcance actualizados.
- Sin cambios en `agents/*`, backend ni virtual keys.
- Trade-off explicito: cualquier PII que pudiera existir dentro de contenido de repo o de snippets de terceros llegaria sin redactar al proveedor; se acepta porque no es el dato del alumno y el proveedor ya recibe ese contenido de todos modos. La redaccion del dato del alumno (evaluador/revisor) se mantiene, y tambien el fail-closed en esas dos llamadas.
