# Design

## Context

Ver `proposal.md` - Why. Lakera corre `pre_call` sobre toda llamada de los agentes (`infra/litellm/config.yaml`), con `default_on: true`. El change archivado `litellm-lakera-guardrail` decidio **bloquear** y acepto explicitamente el riesgo de falsos positivos, dejando escrito que, "si en uso real los falsos positivos resultan frecuentes, el ajuste es ir a `mode: monitor`-equivalente o afinar la politica en la plataforma de Lakera, sin tocar codigo". Este change es ese ajuste.

La investigacion (llamadas directas a `POST https://api.lakera.ai/v2/guard`) aislo el disparador: la palabra `role` en una ruta de fichero marca `prompt_attack` (`flagged=true`, `l4_less_likely`). No es la frase defensiva del prompt ni artefactos como `CLAUDE.md`: es contenido benigno y arbitrario, por lo que ninguna reformulacion de prompt ni filtro de nombres lo evita de forma robusta.

## Goals / Non-Goals

**Goals:**
- Que la deteccion de Lakera nunca bloquee una llamada de agente.
- Mantener la deteccion activa (registro/observabilidad) sobre todas las llamadas.
- Dejar el codigo de los agentes como estaba (sin workarounds que no aportan).

**Non-Goals:**
- Afinar la politica de Lakera en su plataforma (umbral/allowlist): es una via externa, no se toca aqui.
- Anadir mecanismos nuevos de bloqueo (p. ej. un guardrail casero).
- Cambiar `presidio-pii` (sigue en `MASK`, que no bloquea).

## Decisions

**1. `on_flagged: "monitor"` en `lakera-guard`.** La deteccion se sigue ejecutando `pre_call` y registrandose (spans de guardrail en Langfuse), pero no bloquea: la llamada al proveedor continua. Alternativas descartadas: `block` (es el problema actual), `inject_system_message` (inyectaria un aviso al modelo por cada falso positivo, alterando el prompt de negocio), y tocar la politica de Lakera (fuera del repo). `monitor` es la opcion que el propio change archivado dejo prevista.

**2. Revertir los workarounds de esta sesion.** La reformulacion de la frase defensiva y el filtro de listado no atacaban la causa (el disparador es contenido benigno arbitrario como la palabra `role`), asi que se revierten a su estado anterior: menos ruido, sin cambios de codigo innecesarios. El codigo de los agentes vuelve a coincidir con `develop`.

**3. La spec se actualiza, no se ignora.** El requisito de `prompt-injection-mitigation` decia que el sistema SHALL *rechazar* una llamada con inyeccion detectable. Con monitor eso deja de ser cierto, asi que el requisito se modifica para describir el comportamiento real: registrar sin bloquear. Las demas mitigaciones de la spec (tratar el contenido no confiable como dato, delimitarlo) no cambian.

## Risks / Trade-offs

- [Un intento de prompt injection real ya no se bloquea en el proxy] → trade-off explicito de la decision del usuario. Se conservan las demas mitigaciones (delimitacion + instruccion defensiva) y la deteccion queda registrada para observabilidad; volver a bloquear es cambiar una linea de config.
- [Lakera sigue en `pre_call`, asi que se mantiene su latencia en el camino feliz] → mismo coste que antes; no empeora. Con monitor no aporta bloqueo, solo registro.
- [Si Lakera falla o no responde, `pre_call` podria afectar la llamada (fail-closed)] → comportamiento ya existente, no lo cambia este change (el archived `litellm-lakera-guardrail` lo documento).

## Migration Plan

Cambio de configuracion: reconstruir/reiniciar el servicio `litellm` para que relea `config.yaml` (el fichero esta montado como volumen). Sin despliegue de agentes (solo se revierten ficheros a su estado previo). Rollback: poner `on_flagged: "block"` y reiniciar.

## Open Questions

Ninguna.
