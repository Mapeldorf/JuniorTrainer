# Design

## Context

Ver `proposal.md` para la motivacion. Estado tecnico relevante:

- `infra/litellm/provision_keys.py` (propuestas `litellm-virtual-keys` y `litellm-key-budgets`) ya hace *upsert*: crea una key con `max_budget`/`budget_duration` si no existe, y actualiza esos mismos campos en una key existente que no los tenga, dejando intacta una que ya los tiene. El mismo patron de funciones (`_find_key`, `_generate_key`, `_apply_budget`) se puede extender para `rpm_limit` sin cambiar su forma.
- LiteLLM soporta `rpm_limit`/`tpm_limit` nativamente en `/key/generate` y `/key/update` (confirmado contra documentacion oficial, no supuesto): un entero de peticiones por minuto por key, independiente del rate limiting a nivel de modelo (`litellm_params` en `model_list`) o de equipo.
- `agents/*/app/rate_limit.py` ya usa `slowapi` con `DEFAULT_LIMIT = "60/minute"` por IP, documentado en su propio docstring como "cubre con holgura una clase con decenas de alumnos... sin dejar de acotar un bucle de reintentos descontrolado".

## Goals / Non-Goals

**Goals:**
- Que el rate limiting de LiteLLM no sea mas permisivo que el que ya existe en la entrada de cada agente: 60/min en ambos sitios.
- Cambio minimo: extender el script de aprovisionamiento ya existente, sin tocar `config.yaml` ni el codigo de los agentes.

**Non-Goals:**
- No se añade `tpm_limit` (limite por tokens): `slowapi` en los agentes limita por numero de peticiones, no por tokens consumidos; añadir un eje de proteccion distinto (tokens) seria una decision nueva, no una replica de lo que ya existe. Si se quisiera en el futuro, es un campo mas en la misma llamada a `/key/generate`/`/key/update`, no un cambio de diseño.
- No se decide aqui si 60/min es el numero correcto a largo plazo para LiteLLM especificamente (frente a los agentes, que reciben trafico del backend, no directamente de alumnos): se replica el valor ya validado en `agents/*/app/rate_limit.py` por consistencia, no por haberlo recalculado para este punto distinto de la cadena.
- No se toca el rate limiting del backend (`backend/app/rate_limit.py`, 30/min por usuario): es una capa distinta (usuario final vs agente), fuera de alcance de esta propuesta sobre LiteLLM.

## Decisions

- **Extender `_find_key`/`_generate_key`/`_apply_budget` en vez de añadir funciones nuevas paralelas.** Mismo patron que `litellm-key-budgets`: una sola llamada a `/key/generate` o `/key/update` que incluya `max_budget`, `budget_duration` y ahora tambien `rpm_limit`, en vez de una segunda ronda de llamadas solo para el rate limit. Mas simple de razonar: un unico estado "la key esta completamente aprovisionada" en vez de dos checks independientes que podrian desincronizarse.
- **El upsert de `rpm_limit` sigue la misma regla que el de budget: solo actua si falta, nunca si ya hay un valor distinto puesto.** Mismo razonamiento que en `litellm-key-budgets` -- si alguien ajusta el limite a mano para un caso puntual, una re-ejecucion del script no debe pisarlo sin querer.
- **`rpm_limit=60`, literal, no derivado de una formula.** Es el mismo numero que `agents/*/app/rate_limit.py` ya tiene documentado y justificado (holgura para una clase de alumnos, acota un bucle descontrolado); no hay motivo para recalcularlo distinto para LiteLLM cuando el objetivo explicito de esta propuesta es igualar los dos limites.

## Risks / Trade-offs

- [60/min en LiteLLM podria ser mas restrictivo de lo necesario para `agent-exercises`, que podria hacer varias llamadas encadenadas por una sola peticion de generacion] → Mitigacion: es el mismo riesgo que ya existe hoy en el limite de entrada del propio agente (`slowapi`, 60/min); si en uso real resultara insuficiente para algun agente, el ajuste es subir su `rpm_limit` individualmente via `/key/update`, sin afectar a los demas.
- [Doble capa de rate limiting (agente + LiteLLM) con el mismo numero añade una comprobacion redundante en el camino feliz] → Mitigacion: coste despreciable (un contador mas); la redundancia es intencional, igual que la validacion redundante de owner/repo entre backend y agente de codigo -- cada capa protege un perimetro distinto (entrada al agente vs salida hacia el proveedor) aunque el numero coincida hoy.
