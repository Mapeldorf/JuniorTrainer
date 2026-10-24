# Design

## Context

Ver `proposal.md` para la motivacion. Estado tecnico relevante:

- `infra/litellm/provision_keys.py` (propuestas `litellm-agent-keys`,
  `litellm-key-budgets`, `litellm-key-rate-limit`) crea 6 virtual keys via
  `POST /key/generate` con `max_budget=5`/`budget_duration=30d`/`rpm_limit=60`, y es
  idempotente por `key_alias` con *upsert* por campo: crea si falta, rellena un campo
  ausente via `POST /key/update`, y deja intacta una key que ya tiene todos los
  campos. `_MAX_BUDGET_USD = 5` es hoy una constante de modulo.
- El change archivado `litellm-key-budgets` decidio expresamente el importe fijo en el
  script "no en variables de entorno", dejando anotado que se revisaria "si se
  necesitara variar el importe por entorno (desarrollo vs produccion)". Este change es
  esa revision: ya se necesita (5 en desarrollo, 50 en produccion).
- Ya hay precedente de parametros de este script leidos del entorno:
  `LITELLM_MASTER_KEY` (obligatoria, el script sale con error si falta) y
  `LITELLM_BASE_URL` (opcional, con valor por defecto). La nueva variable sigue el
  mismo patron que `LITELLM_BASE_URL`: opcional, con defecto.

## Goals / Non-Goals

**Goals:**
- Un unico valor de `max_budget` que sea 5 USD en desarrollo (por defecto, sin tocar
  nada) y 50 USD en produccion (exportando una variable), sin editar el codigo.
- Fallar pronto y claro ante un valor mal escrito, antes de tocar el proxy.
- Conservar intactas las invariantes del script: idempotencia por alias y no
  sobrescribir un `max_budget` ya puesto.

**Non-Goals:**
- No se cambia `budget_duration` (sigue `30d`) ni `rpm_limit` (sigue 60, su propia
  constante).
- No se hace que el script sobrescriba el budget de una key que ya tiene uno: si un
  proxy de desarrollo tiene keys a 5 y se pone la variable a 50, esas keys no cambian
  (produccion se aprovisiona fresca, o el operador ajusta a mano). Cambiar esa
  invariante seria otra decision.
- No se reconcilia aqui el texto del capstone: va despues del archivado, segun el
  flujo del proyecto.
- No se decide el importe de produccion dentro del codigo: 50 USD es el dimensionado
  del capstone y se aporta por entorno; cambiarlo es cambiar la variable, no el
  codigo.

## Decisions

- **El `max_budget` se lee de `LITELLM_KEY_MAX_BUDGET_USD`, con 5.0 por defecto.**
  Nombre explicito (prefijo `LITELLM_KEY_`, igual que el resto de parametros del proxy
  llevan prefijo `LITELLM_`) para no confundirlo con los presupuestos de operacion de
  los agentes (5 busquedas, 10 ficheros) ni con `max_budget` de otros contextos.
  Alternativa descartada: un flag de linea de comandos (`--max-budget`); se descarta
  porque el script se invoca desde el arranque del stack y lo natural en ese contexto
  es una variable de entorno, como las otras dos que ya lee.
- **La validacion vive en `main()`, no en el import.** Se lee y valida el valor al
  principio de `main()`, junto a la comprobacion de `LITELLM_MASTER_KEY`, para poder
  salir con `return 1` y un mensaje `Error: ...` en vez de un traceback al importar.
  Un valor no numerico o <= 0 aborta antes de cualquier llamada al proxy.
- **`_generate_key` y `_missing_fields` reciben el `max_budget` como parametro.** En
  vez de leer una constante global, el valor validado se pasa desde `main()`. Asi la
  logica de creacion y de upsert queda sin estado global de entorno y es testeable sin
  red: un test puede llamar `_missing_fields(existing, models, max_budget=50)` y
  comprobar el resultado.
- **Se mantiene el upsert "solo rellena lo que falta".** `_missing_fields` sigue
  escribiendo `max_budget` solo cuando `existing["max_budget"] is None`. El valor que
  escribe es el vigente (el de la variable), pero no toca una key que ya tenga
  cualquier budget. Esto preserva la decision del change anterior de no pisar un ajuste
  manual, y evita que un cambio de entorno reescriba keys existentes.

## Risks / Trade-offs

- [Un proxy de desarrollo ya provisionado con keys a 5 USD no pasa a 50 con solo
  cambiar la variable, porque el upsert no sobrescribe budgets existentes] →
  Aceptado: produccion es un proxy distinto que se aprovisiona fresco (keys nuevas con
  50 desde la creacion). Para forzar un cambio de importe en keys existentes, el
  operador las ajusta a mano (`/key/update`) o las revoca y reaprovisiona, igual que
  hoy. Documentado en la cabecera del script.
- [La variable mal escrita (p. ej. `50 USD`, `cincuenta`, `-5`) podria crear keys con
  un budget absurdo] → Mitigado: se valida que sea un numero > 0 y, si no, el script
  sale con error sin tocar ninguna key.
