# Proposal

## Why

El agente validador aplica hoy la misma comprobacion -- incluido el chequeo semantico de duplicados contra el catalogo (`validador-duplicados-tecnologias`) -- tanto al dar de alta una tecnologia nueva como al validar las tecnologias de una generacion de ejercicios. En la generacion, las tecnologias ya existen en el catalogo por diseno (el tech lead las elige de un selector poblado desde ahi), asi que el validador las marca como "duplicado de si mismas" y rechaza la generacion. Reproducido en vivo: `validate_technologies(["RxJS en Angular"])` devuelve `valid=False` con `duplicate_technologies=[{"input": "RxJS en Angular", "matches": "RxJS en Angular"}]`, porque esa tecnologia ya esta en el catalogo -- esto bloquea cualquier generacion que use una tecnologia ya existente, es decir, casi todas.

## What Changes

- El validador distingue dos contextos de llamada, indicados explicitamente en la peticion A2A:
  - **Alta de tecnologia** (`POST /technologies`): comprueba que la entrada es una tecnologia de programacion Y que no duplica semanticamente ninguna tecnologia ya existente en el catalogo. Comportamiento actual, sin cambios.
  - **Generacion de ejercicios** (`POST /generations`): comprueba UNICAMENTE que la entrada es una tecnologia de programacion. No consulta el catalogo ni pide al modelo la comparacion de duplicados.
- `backend/app/routers/technologies.py` sigue pidiendo la comprobacion completa (con duplicados).
- `backend/app/orchestrator.py` (`_call_validator`) pide la comprobacion sin duplicados.
- El contrato de entrada A2A del validador incorpora un campo explicito para el contexto de la llamada; sin ese campo (o en un valor no reconocido), el validador sigue haciendo la comprobacion completa (con duplicados) por defecto -- el mismo comportamiento fail-safe que ya tenia antes de esta propuesta, para que una llamada antigua o mal formada no se vuelva mas permisiva por omision.
- `duplicate_technologies` en la respuesta queda siempre vacio cuando no se pide la comprobacion de duplicados (nunca se omite el campo, para no romper a quien ya lo lee).

## Capabilities

### Modified Capabilities
- `technology-validation`: la comprobacion semantica de duplicados contra el catalogo deja de aplicarse siempre que se valida una lista de tecnologias; pasa a aplicarse solo cuando la llamada indica el contexto de alta de tecnologia, nunca en la validacion previa a una generacion.

## Impact

- `agents/validator/app/input.py`: parsear el nuevo campo de contexto del mensaje A2A entrante.
- `agents/validator/app/service.py`: `validate_technologies` deja de consultar el catalogo y de pedir la comparacion de duplicados cuando el contexto es "generacion"; ajuste del prompt y/o del `response_format` segun el contexto.
- `agents/validator/app/executor.py`: pasar el contexto parseado a `validate_technologies`.
- `backend/app/routers/technologies.py`: enviar el contexto "alta de tecnologia" en la peticion A2A.
- `backend/app/orchestrator.py`: enviar el contexto "generacion" en la peticion A2A.
- `openspec/specs/technology-validation/spec.md`: separar los requisitos de comprobacion de duplicados por contexto.
- `agents/validator/scripts/verify_validator.py`: cubrir ambos contextos.
- `docs/especificacion-agentes.md` y `docs/especificacion-backend.md`: si describen el comportamiento actual del validador, actualizar la descripcion.
- Sin cambios de esquema en base de datos ni en el rol `agents_validator_reader`.
