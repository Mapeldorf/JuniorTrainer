# Proposal

## Why

Una generacion real de ejercicios fallo entera con `el agente de codigo ha fallado: fallo llamando al agente en http://agent-code:8011/: no se pudo leer ningun fichero de los elegidos por el modelo`. La traza de Langfuse muestra la causa: el guardrail `presidio-pii` (`pre_call`, `MASK`) enmascara las entidades `URL` y `PERSON` **dentro del listado de ficheros del repositorio** que el agente de codigo manda al modelo.

Sobre rutas e identificadores de codigo esas dos entidades disparan cientos de falsos positivos:

- `src/app/core/services/auth.service.ts` -> `src/app/core/services/<URL>rvice.ts`
- `card.component.ts` -> `card/<PERSON>ponent.ts`

El prompt de sistema pide copiar las rutas "tal cual de la lista recibida", asi que el modelo devuelve rutas ya enmascaradas; el agente las valida contra el listado real del commit, ninguna coincide y no lee ningun fichero.

Ademas, el mismo guardrail corrompe el **output** de los agentes: LiteLLM deja `presidio_filter_scope` en su valor por defecto `"both"`, que añade un callback de salida (`apply_to_output=True`) y enmascara tambien la respuesta del modelo. El texto generado de los ejercicios sale con marcadores incrustados (`<PERSON>` en mitad de una frase). Ese output masking no aporta proteccion real -- el proveedor ya vio el input, ya redactado -- y solo corrompe el contenido que devolvemos a la app.

## What Changes

- `infra/litellm/config.yaml`: en `pii_entities_config` del guardrail `presidio-pii`, quitar `URL` y `PERSON`. Se mantienen `EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `IP_ADDRESS`, `IBAN_CODE` (todas por regex, sin falsos positivos sobre codigo).
- `infra/litellm/config.yaml`: añadir `presidio_filter_scope: "input"` al guardrail `presidio-pii`, para que la redaccion actue solo sobre el input y no sobre la respuesta del modelo.
- `openspec/specs/pii-redaction/spec.md`: actualizar Purpose y el requisito (cubre email, telefono, tarjeta, IP e IBAN; no URL ni nombre de persona) y añadir el requisito de que el output no se redacta.
- Sin cambios en `agents/*` ni en el backend: era un conflicto de configuracion, no de codigo.

## Capabilities

### Modified Capabilities
- `pii-redaction`: el conjunto de entidades redactadas se reduce a las de riesgo real que no colisionan con contenido de repositorio, y la redaccion pasa a aplicarse solo al input (no al output del modelo).

## Impact

- `infra/litellm/config.yaml`: 2 entidades menos en `pii_entities_config` + `presidio_filter_scope: "input"`.
- `openspec/specs/pii-redaction/spec.md`: requisitos y Purpose actualizados.
- Trade-off explicito: URLs y nombres de persona dejan de redactarse hacia el proveedor, y el output del modelo ya no se enmascara. Se acepta porque `URL` no es un dato personal, `PERSON` sobre codigo/rutas era inviable, y el output masking no evitaba ninguna fuga hacia el proveedor; el dato personal de riesgo real en las respuestas de alumno (email, telefono) sigue redactandose en el input.
