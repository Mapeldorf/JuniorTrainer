# Proposal

## Why

El techo de gasto por virtual key (`max_budget`) esta hoy incrustado como la
constante `_MAX_BUDGET_USD = 5` en `infra/litellm/provision_keys.py`. Esos 5 USD
son la proteccion personal del autor en desarrollo, pero el capstone dimensiona el
tope de despliegue en 50 USD (§3.4, §3.8 punto 8, §6.2 control 15), porque a escala
de organizacion el pico de 30 dias de la clave mas cargada (el revisor) supera los
5 USD. El propio texto deja constancia de que alinear `provision_keys.py` con ese
valor "es un cambio pendiente", y el change archivado `litellm-key-budgets` ya
anticipo esta revision ("si se necesitara variar el importe por entorno
—desarrollo vs produccion— en el futuro, se revisaria esta decision").

Con el importe fijo, o el desarrollo pierde su proteccion de 5 USD (si se sube a
50), o el script se queda corto para produccion (si se deja en 5). Hace falta un
unico valor que sea 5 en desarrollo y 50 en produccion sin editar el codigo.

## What Changes

- `infra/litellm/provision_keys.py`: el `max_budget` deja de ser una constante fija
  y se lee de una variable de entorno nueva, `LITELLM_KEY_MAX_BUDGET_USD`, con **5
  USD por defecto** (desarrollo). El despliegue de produccion exporta
  `LITELLM_KEY_MAX_BUDGET_USD=50`. `budget_duration` sigue siendo `30d`.
- El script valida el valor antes de llamar al proxy: si la variable no es un numero
  mayor que 0, termina con error sin crear ni modificar ninguna key (mismo patron
  que la comprobacion de `LITELLM_MASTER_KEY`).
- Se conserva la invariante de *upsert* existente: el script solo escribe el
  `max_budget` al crear una key o al rellenar una key que no tiene ninguno; **nunca
  sobrescribe** un `max_budget` ya puesto, aunque difiera del vigente. Desarrollo y
  produccion son proxies LiteLLM distintos, asi que un cambio de la variable no pisa
  las keys ya aprovisionadas en el otro entorno.
- Sin cambios en `agents/*`: superar el presupuesto sigue bloqueando la key
  (HTTP 422 `budget_exceeded`) y la llamada falla como cualquier otro error del
  proveedor que los agentes ya propagan.

## Capabilities

### Modified Capabilities
- `litellm-agent-keys`: el techo de gasto por key pasa de un importe fijo de 5 USD a
  un importe configurable por entorno (5 USD por defecto), afectando a los requisitos
  "Techo de gasto por key", "Aprovisionamiento con budget desde la creacion" y "Keys
  existentes sin budget se actualizan, no se omiten".

## Impact

- `infra/litellm/provision_keys.py`: lectura y validacion del nuevo valor en `main()`;
  `_generate_key` y `_missing_fields` reciben el `max_budget` como parametro en vez de
  leer la constante.
- `infra/litellm/test_provision_keys.py` (nuevo): test de la biblioteca estandar que
  cubre el valor por defecto, el valor de produccion, los valores invalidos y la
  invariante de no sobrescribir un budget ya puesto, sin red ni proxy.
- Sin cambios en `agents/*`, el backend ni ningun schema.
- La reconciliacion del texto del capstone (§3.4, §3.8, §6.2) para describir la
  variable queda **fuera de este change**: se hace despues, tras archivar, segun el
  flujo del proyecto.
