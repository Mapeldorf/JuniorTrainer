# Proposal

## Why

Lakera Guard bloqueaba con `400` llamadas legitimas de los agentes: su detector `prompt_attack` marca como ataque contenido benigno (comprobado contra la API de Lakera: la sola palabra `role`, presente en rutas de repositorio como `role.guard.ts`, se marca como `prompt_attack` en el nivel de confianza mas bajo, `l4_less_likely`). El bloqueo rompia la generacion de ejercicios con repositorio. Decision del usuario: **Lakera debe solo monitorizar, nunca bloquear**.

## What Changes

- `infra/litellm/config.yaml`: el guardrail `lakera-guard` pasa a `on_flagged: "monitor"` — la deteccion se sigue ejecutando y registrando, pero no bloquea ninguna llamada.
- Se **revierte** el intento de arreglo de esta sesion (reformular la frase defensiva en los 4 prompts y filtrar el listado de ficheros en el agente de codigo): no atacaba la causa real y ya no es necesario.
- Se actualiza la spec `prompt-injection-mitigation`: la deteccion automatizada en el proxy pasa de **rechazar** la llamada a **observar sin bloquear**.

## Capabilities

### New Capabilities
Ninguna.

### Modified Capabilities
- `prompt-injection-mitigation`: el requisito "Deteccion automatizada de prompt injection en el proxy" cambia de "rechazar la llamada antes de invocar al proveedor" a "registrar la deteccion sin bloquear la llamada" (modo monitor).

## Impact

- `infra/litellm/config.yaml`: `on_flagged: "monitor"` en `lakera-guard`.
- Reversion de `agents/code/app/service.py`, `agents/web/app/service.py`, `agents/evaluator/app/service.py` y `agents/reviewer/app/service.py` a su estado anterior (prompts originales, sin el filtro `_is_selectable`).
- Spec `prompt-injection-mitigation`.
- Sin cambios en backend, frontend ni en la API.
