# Design

## Context

`agents/validator/app/service.py` (`validate_technologies`) hace hoy, siempre, la misma secuencia: consulta el catalogo completo (`app/tools/technology_catalog.py`), construye un unico prompt que pide al modelo tanto "es tecnologia de programacion" como "duplicado semantico contra el catalogo", y aplica la misma coherencia defensiva a ambos. No distingue si la llamada viene de `backend/app/routers/technologies.py` (alta de una tecnologia nueva) o de `backend/app/orchestrator.py` (`_call_validator`, puerta previa a cada generacion).

En la generacion, las tecnologias de entrada ya existen en el catalogo por diseño: el formulario de generacion las ofrece via un selector (`TechnologyMultiselectComponent`) poblado desde `GET /technologies`, no como texto libre. La comprobacion de duplicados, pensada para el alta (evitar que "TS" se cuele si ya existe "TypeScript"), compara entonces cada tecnologia contra un catalogo que ya la contiene a ella misma, y el modelo la señala como duplicado de si misma -- rechazo sistematico, reproducido en vivo con `validate_technologies(["RxJS en Angular"])`.

El change previo `validador-duplicados-tecnologias` acepto a proposito que la comprobacion de duplicados tambien afectase a la generacion (ver su design.md, "Trade-offs"), pensando en el caso de un nombre no canonico que coincide con una variante ya existente (p. ej. pedir "Angular" cuando el catalogo solo tiene "Angular Framework"). No contemplo el caso -- el real, y el habitual -- de que la entrada sea exactamente el nombre canonico ya existente. Esta propuesta revierte esa decision explicitamente: en generacion, el validador deja de comparar contra el catalogo por completo.

Ver proposal.md - Why para la motivacion completa.

## Goals / Non-Goals

**Goals:**
- El validador se comporta de forma distinta segun quien lo llama, sin adivinarlo: el llamador lo indica de forma explicita en la peticion A2A.
- El alta de tecnologias (`technologies.py`) sigue teniendo exactamente el mismo comportamiento que hoy (tecnologia de programacion + duplicado semantico).
- La generacion (`orchestrator.py`) deja de poder fallar por "duplicado de si misma": solo falla si alguna entrada no es una tecnologia de programacion, o por un fallo generico del validador (transporte, timeout, guardarrail, respuesta invalida).
- Una peticion sin el campo de contexto, o con un valor no reconocido, se comporta igual que hoy (comprobacion completa, con duplicados) -- nadie puede volverse mas permisivo por omitir un campo nuevo.

**Non-Goals:**
- No se toca el comportamiento del alta de tecnologias en si (sigue intacto: 409 por duplicado exacto o semantico, 422 por no ser tecnologia de programacion).
- No se toca el rol `agents_validator_reader` ni la tabla `public.technology`: la consulta al catalogo sigue siendo la misma, solo deja de hacerse cuando el contexto es "generacion".
- No se introduce un tercer contexto ni un mecanismo generico de configuracion por llamada: solo los dos contextos que ya existen hoy como llamadores (alta, generacion).
- No se cambia el limite de una tecnologia por llamada que ya aplica el alta (`NewTechnologyRequest`); sigue siendo una lista de una sola entrada en ese caso.

## Decisions

### D1: Un campo `context` en el payload A2A, con dos valores reconocidos
La peticion A2A al validador (`{"technologies": [...]}`) incorpora un campo hermano `context`, con los valores `"catalog_entry"` (alta de una tecnologia, comportamiento actual) y `"generation"` (validacion previa a una generacion, sin duplicados). Cualquier otro valor, o su ausencia, se trata igual que `"catalog_entry"` -- es el comportamiento de hoy, asi que es el default seguro (fail-safe: una llamada antigua, o un valor corrupto, nunca se vuelve mas permisiva).

Alternativa descartada: inferir el contexto por la forma de la entrada (p. ej. "una sola tecnologia = alta"). Se descarta porque un alta siempre manda una lista de una sola tecnologia pero nada impide que una generacion tambien se pida con una sola tecnologia -- la forma de la entrada no determina el contexto de forma fiable, y el llamador ya sabe perfectamente cual es.

Alternativa descartada: dos skills/endpoints A2A distintos (`validar_alta`, `validar_generacion`) en vez de un campo en el mismo payload. Se descarta por ser un cambio mayor de superficie (agent card, routing, documentacion) para una diferencia que es puramente de comportamiento interno, no de contrato de transporte; un campo en el mismo mensaje es coherente con como ya se extiende este payload (ver `trace_id` en metadata).

### D2: `validate_technologies` recibe el contexto y decide ahi si consulta el catalogo
`agents/validator/app/input.py` (`parse_technologies` o una funcion hermana) extrae `context` del mensaje A2A igual que ya extrae `technologies`, normalizandolo al enum de dos valores con el default de D1. `app/executor.py` pasa ese valor a `validate_technologies(technologies, context, trace_id)`.

Dentro de `service.py`, cuando `context == "generation"`:
- no se llama a `list_catalog_technologies()` (ni se abre conexion a Postgres),
- el prompt (`_SYSTEM_PROMPT`) no incluye el catalogo ni el criterio de duplicados, solo el criterio de "es tecnologia de programacion",
- `_RESPONSE_FORMAT` se simplifica a los campos `valid`/`reason`/`invalid_technologies` (sin `duplicate_technologies`).

`ValidationResult.duplicate_technologies` sigue existiendo siempre en el modelo (`app/models.py`), con su default `[]`; en contexto `generation` nunca se rellena, asi que el campo llega vacio en la respuesta A2A en vez de desaparecer -- ningun llamador que ya lo lea (`technologies.py`) se rompe por su ausencia porque ese llamador siempre pide `catalog_entry`.

Alternativa descartada: mantener siempre la misma consulta al catalogo y el mismo esquema, y simplemente ignorar `duplicate_technologies` en `orchestrator.py`. Se descarta porque no resuelve el problema: el modelo seguiria viendo el catalogo y señalando el duplicado, y `valid` seguiria viniendo en `false` por la coherencia defensiva ya existente (D4 del change anterior) -- hay que dejar de pedirle la comparacion, no solo ignorar una parte de la respuesta.

### D3: `technologies.py` pasa `context="catalog_entry"`, `orchestrator.py` pasa `context="generation"`
Un unico punto de cambio en cada llamador: el diccionario que ya construyen (`{"technologies": [...]}`) incorpora `"context": "catalog_entry"` en `backend/app/routers/technologies.py` y `"context": "generation"` en `backend/app/orchestrator.py` (`_call_validator`). Sin cambios en `send_a2a_task` ni en `A2ATaskError`: siguen siendo payloads de datos genericos.

## Risks / Trade-offs

- **[Riesgo] Un llamador nuevo, futuro, olvida pasar `context`** y hereda sin darse cuenta el comportamiento de alta (con duplicados) en un flujo pensado para solo validar tecnologia-de-programacion → **Mitigacion**: el default fail-safe (D1) nunca permite un falso negativo de seguridad (en el peor caso, un rechazo de mas, nunca un `valid=true` indebido); el nombre del campo y sus dos valores quedan documentados en `openspec/specs/technology-validation/spec.md`, visible para cualquier futuro llamador.
- **[Riesgo] Divergencia de prompts**: mantener dos variantes del `_SYSTEM_PROMPT`/`_RESPONSE_FORMAT` (con y sin duplicados) puede desincronizarse si se edita solo una → **Mitigacion**: ambas variantes comparten el bloque de instrucciones sobre "es tecnologia de programacion" (sin duplicar ese texto), y solo la seccion de duplicados se añade u omite condicionalmente; se cubre con un caso de `verify_validator.py` por cada contexto.
- **[Trade-off] Se revierte parte de una decision explicita del change anterior** (que la generacion con un nombre no canonico, variante de uno ya existente, tambien fallase) → se acepta a proposito: el caso real observado es el nombre canonico exacto, no una variante, y bloquear ahi es un falso rechazo sistematico en el camino mas comun del sistema (generar ejercicios sobre tecnologias que ya estan en el catalogo), mientras que el caso de variante no canonica en generacion no se ha observado y no justifica mantener roto el camino principal.

## Migration Plan

1. Cambios en `agents/validator` (input, service, models si hiciera falta, executor) para aceptar y aplicar `context`, con el default fail-safe de D1.
2. Cambios en `backend` (`technologies.py`, `orchestrator.py`) para enviar el `context` correspondiente.
3. Actualizar `agents/validator/scripts/verify_validator.py` para cubrir ambos contextos (duplicados activos en `catalog_entry`, ausentes en `generation`).
4. Desplegar agente y backend juntos: mientras no se despliega el backend, el agente actualizado sigue recibiendo peticiones sin `context` y las trata como `catalog_entry` (comportamiento actual, sin romper nada); mientras no se despliega el agente, el backend enviando `context` a una version antigua del agente no tiene efecto porque esa version lo ignora. No hay ventana de incompatibilidad en ningun orden de despliegue.
5. Rollback: revertir el despliegue de ambos lados a la version anterior; no hay cambios de esquema de base de datos ni de datos persistidos que revertir.
