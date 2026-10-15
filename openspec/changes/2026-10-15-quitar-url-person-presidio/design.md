# Design

## Context

Ver `proposal.md` - Why. El guardrail `presidio-pii` (change archivado `2026-10-15-litellm-presidio-pii-masking`) corre `pre_call` con `MASK` sobre `EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `IP_ADDRESS`, `IBAN_CODE`, `URL` y `PERSON`. El agente de codigo (`agents/code/app/service.py`) manda al modelo el listado completo de rutas del repositorio para que elija hasta 10 ficheros, y le pide copiarlas literalmente.

La traza de Langfuse lo confirma: el input de `litellm:agent-code` aparece lleno de `<URL>...`/`<PERSON>...` y su output copia literalmente `"src/app/core/services/<URL>rvice.ts"`. No es el masking de Langfuse -- en esa llamada `mask_input` no esta activo (el trace mostraria `redacted-by-litellm`), luego el texto enmascarado es el que de verdad salio hacia el proveedor.

El mismo guardrail corrompe tambien el output. En LiteLLM, `initialize_presidio` (`guardrail_initializers.py`) hace `filter_scope = explicit_filter_scope or "both"`; sin `presidio_filter_scope` explicito, `run_output` es `True` y se registra un `mask_output_callback` con `apply_to_output=True`. En la traza aparecen spans del guardrail en `guardrail_mode: ["post_call"]` con `guardrail_masked_entity_count: {"PERSON": N}` justo tras cada generacion, y el texto generado sale con `<PERSON>` incrustado. Lo que controla el output no es `mode: pre_call` (eso fija el hook de entrada) sino `filter_scope`.

## Goals / Non-Goals

**Goals:**
- Que el listado de rutas del repositorio y el contenido generado por el modelo lleguen intactos, sin romper la redaccion de PII de riesgo real en el input.
- Cambio minimo, solo configuracion.

**Non-Goals:**
- No se toca el codigo del agente de codigo (`_pick_files`, validacion de rutas). La validacion contra el listado real del commit ya es la defensa correcta; el fallo era que la entrada ya venia corrupta.
- No se redefine el catalogo completo de entidades de Presidio.
- No se cambia `EMAIL_ADDRESS`/`PHONE_NUMBER`/`CREDIT_CARD`/`IP_ADDRESS`/`IBAN_CODE`, que son las de riesgo real.
- No se enmascara el output del modelo: no es el modelo de amenaza de la spec y rompia los ejercicios.

## Decisions

**1. Quitar `URL` y `PERSON`, mantener las entidades por regex.** Las cinco entidades que se mantienen son reconocedores de patron (email, telefono, tarjeta, IP, IBAN): no dependen del idioma ni colisionan con extensiones de fichero, rutas o identificadores. `URL` no es un dato personal en si mismo y es el principal generador de falsos positivos (`.ts`, `.gr`, `.properties`...). `PERSON` es PII real, pero el reconocedor por defecto (modelo en ingles) marca palabras sueltas de codigo (`component`) y sobre el listado de rutas el daño (romper la seleccion de ficheros) supera el beneficio.

**2. `presidio_filter_scope: "input"`.** Fija la redaccion al input (lo que de verdad importa: el dato del alumno antes de salir al proveedor) y desactiva el `mask_output_callback`. No altera el fail-closed (con `pii_entities_config` poblado, presidio.py:457 sigue forzando 500 si Presidio no responde) ni toca `lakera-guard`.

**3. Se actualiza la spec, no se ignora.** Igual que en `2026-10-15-fix-falso-positivo-lakera`: el requisito de `pii-redaction` listaba `URL` y nombre de persona; se modifica para describir el comportamiento real, y se añade el requisito de que el output no se redacta. Revertir es cambiar lineas de config y la spec.

## Risks / Trade-offs

- [Un nombre de persona real escrito en una respuesta de alumno ya no se redacta antes de salir al proveedor] → trade-off explicito. El reconocedor en ingles tenia recall imperfecto y cortaba mal (`alum[MASKED NAME]`, documentado en el change archivado); los datos de contacto (email, telefono), que son el vector de fuga mas sensible en la practica, siguen cubiertos.
- [Una URL real dentro de una respuesta de alumno ya no se redacta] → `URL` no es, por definicion, un dato personal; el coste de mantenerlo (rompia la generacion) supera con creces el beneficio.
- [El output del modelo ya no se enmascara: si el modelo generara PII real (memorizada/alucinada), llegaria a la app tal cual] → no es el modelo de amenaza de la spec (que cubre el dato real del alumno en el input) y, si el input iba redactado, el modelo no dispone del valor real para repetirlo. A cambio se elimina la corrupcion del contenido generado.

## Migration Plan

Cambio de configuracion: recrear `litellm` (`docker compose up -d --force-recreate litellm`) para que relea `config.yaml` montado por volumen. Rollback: volver a anadir `URL: "MASK"` / `PERSON: "MASK"` y/o quitar `presidio_filter_scope` (vuelve a `"both"`), y recrear. Sin despliegue de agentes.

## Open Questions

Ninguna.
