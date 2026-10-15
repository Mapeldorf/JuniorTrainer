# Proposal

## Why

Hoy el unico control de privacidad sobre el contenido real de las llamadas es el `mask_input`/`mask_output` de Langfuse (propuesta `agent-trace-privacy`, ya archivada): oculta la traza *completa* en el panel de observabilidad, pero el texto sigue viajando intacto hasta el proveedor del LLM. Si un alumno escribe sin querer un dato personal real (su email, su telefono, su nombre completo) en una respuesta, ese dato sale de la infraestructura del proyecto tal cual, sin ninguna redaccion.

## What Changes

- `docker-compose.yml`: dos servicios nuevos, `presidio-analyzer` y `presidio-anonymizer` (imagenes oficiales de Microsoft), solo accesibles dentro de la red interna (igual que los agentes: sin puerto publicado al host).
- `infra/litellm/config.yaml`: guardrail `presidio-pii` (`guardrail: presidio`, `mode: pre_call`, `default_on: true`) -- corre automaticamente en toda llamada de los 5 agentes, junto al guardrail de Lakera ya existente. Entidades enmascaradas (`MASK`, no `BLOCK`): `EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `IP_ADDRESS`, `IBAN_CODE`, `URL`, `PERSON`.
- Sin cambios en `agents/*`: el enmascarado ocurre dentro de LiteLLM antes de reenviar la llamada al proveedor; el texto que llega al modelo ya tiene los datos personales sustituidos por un marcador generico (p. ej. `[MASKED EMAIL]`, formato real del anonymizer por defecto, confirmado en verificacion).
- **Decision explicita de alcance**: se usa la imagen oficial de `presidio-analyzer` con su modelo de idioma por defecto (ingles), no una imagen propia con modelo en español. Los alumnos escriben en español, asi que la deteccion de `PERSON` (nombres) tendra peor recall que con un modelo en español -- se acepta como limitacion conocida de esta primera iteracion, documentada en design.md. Los patrones universales (email, telefono, tarjeta, IP, IBAN, URL) no dependen del idioma y funcionan igual de bien.

## Capabilities

### New Capabilities
- `pii-redaction`: datos personales reales dentro del contenido de una llamada se sustituyen por un marcador generico antes de que esa llamada salga hacia el proveedor del LLM.

## Impact

- `docker-compose.yml`: 2 servicios nuevos (`presidio-analyzer`, `presidio-anonymizer`).
- `infra/litellm/config.yaml`: nueva entrada en `guardrails`.
- Sin cambios en `agents/*/app/*.py` ni en `backend/*`.
- Sin credencial nueva: Presidio se autoaloja, sin API key ni coste por llamada (a diferencia de Lakera).
