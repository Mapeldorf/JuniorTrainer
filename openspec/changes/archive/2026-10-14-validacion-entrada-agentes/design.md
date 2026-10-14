# Design

## Context

Dos defensas en profundidad ya establecidas en el proyecto sirven de precedente directo para este cambio:
- `agents/exercises/app/input.py:45` revalida `count` (1-5) aunque `backend/app/schemas/generation.py:29` ya lo acota con Pydantic -- el agente no confia en que el unico llamador posible (el backend) sea siempre correcto.
- `backend/app/schemas/generation.py` valida `owner`/`repo` con `validate_owner_or_repo` (`backend/app/github_ref.py`) antes de crear la generacion; `agents/code/app/github_ref.py` tiene una copia byte-a-byte de esa misma funcion, pero nunca la invoca -- es el unico de los tres pares entrada/agente que no sigue el patron de revalidacion.

Las rutas A2A de los 5 agentes, incluida la Agent Card, ya exigen la credencial de servicio del change `autenticacion-backend-agentes`; este cambio no toca esa capa, es una defensa adicional para cuando la peticion SI esta autenticada pero el payload es invalido (bug del backend, o una superficie de entrada futura que reutilice el agente).

Los executors de los 3 agentes de generacion dejan que las excepciones de `parse_*` (p. ej. `InvalidExercisesAgentInput`) se propaguen sin capturarlas (`agents/exercises/app/executor.py:25`); el SDK A2A (`DefaultRequestHandler`) es quien las convierte en una respuesta de error de la tarea. Este cambio sigue ese mismo patron, sin tocar los executors.

Ver proposal.md - Why para la motivacion completa.

## Goals / Non-Goals

**Goals:**
- El agente de codigo valida `owner`/`repo` con la misma regla que el backend, sin depender de el.
- El backend y el agente web comparten el mismo limite de numero/longitud de tecnologias, revalidado de forma independiente en el agente (mismo patron que `count` en el agente de ejercicios).
- Limites explicitos y documentados (no "razonablemente grande"): max 15 tecnologias por generacion, max 60 caracteres por tecnologia.

**Non-Goals:**
- No se cambia el mecanismo de autenticacion backend-agente (ya resuelto en `autenticacion-backend-agentes`).
- No se toca el filtrado de `path` dentro de un repositorio (ya resuelto en `validar-path-agente-codigo`).
- No se anade un catalogo cerrado de tecnologias ni canonicalizacion semantica (discutido en conversacion previa, descartado por ahora).

## Decisions

### Limites elegidos: 15 tecnologias, 60 caracteres cada una

**Alternativas consideradas:** un limite mas bajo (p. ej. 5) arriesga rechazar generaciones legitimas con un stack amplio (frontend + backend + libreria + testing + CI); un limite mas alto (p. ej. 50) deja demasiado margen de coste en Tavily/LLM sin beneficio real -- ninguna generacion observada en el proyecto (ver ejemplos en specs/scripts existentes: "Git", "React, FastAPI", "Angular, RxJS") pasa de un puñado de tecnologias.

**Elegido:** 15 tecnologias (margen amplio sobre el uso real, sin ser ilimitado) y 60 caracteres por tecnologia (cubre frases como "Observables en Angular" o "Testing con Jest y Cypress" con margen, sin permitir parrafos enteros coma-separados que inflen el prompt).

### Donde se aplica cada limite

- **Backend** (`StartGenerationRequest.technologies`, `backend/app/schemas/generation.py`): un `field_validator` adicional que comprueba `len(value) <= 15` y que cada elemento (ya recortado de espacios por el validador existente) no supere 60 caracteres. Es el punto de entrada real del sistema: una peticion fuera de limite nunca llega a crear una fila de `generation` (422 de FastAPI, mismo patron que `count`).
- **`agents/web`** (`parse_technologies`, `agents/web/app/input.py`): misma comprobacion (15 elementos, 60 caracteres), aplicada DESPUES de `_normalize` (que ya deduplica y recorta espacios) y ANTES de devolver la lista al executor -- si se excede, lanza `InvalidTechnologiesInput` (nueva, mismo estilo que `InvalidCodeAgentInput`/`InvalidExercisesAgentInput`), que el executor deja propagar sin capturarla, igual que ya hace con el resto de errores de parseo.
- **`agents/code`** (`parse_repo_input`, `agents/code/app/input.py`): tras el `.strip()` ya existente de `owner`/`repo`, llama a `validate_owner_or_repo` (importada de `agents/code/app/github_ref.py`, que ya existe y no cambia) y relanza `InvalidGitHubRef` como `InvalidCodeAgentInput` para que el llamador solo tenga que distinguir un tipo de excepcion de este modulo, igual que ya hace con los demas campos.

Los dos limites de tecnologias (backend y `agents/web`) se definen como constantes en cada fichero (no se comparte una constante entre repositorios/servicios, mismo criterio que `count` 1-5 hoy: cada lado tiene su propia copia literal del mismo valor, documentada con un comentario que remite al otro lado).

## Risks / Trade-offs

- **[Riesgo] Los dos limites de tecnologias (backend, agente web) pueden desincronizarse en el futuro** si alguien cambia uno sin el otro. → *Mitigacion*: mismo riesgo que ya existe hoy con `count` 1-5 (backend y agente de ejercicios), aceptado como patron establecido del proyecto; un comentario en cada constante remite al otro lado.
- **[Trade-off] 15/60 son valores arbitrarios, no derivados de un requisito de producto explicito.** Aceptado: son limites de seguridad/coste (evitar abuso), no de UX: lo importante es que exista un techo razonable y documentado, no el valor exacto. Pueden ajustarse despues sin romper la forma del requisito.
- **[Riesgo] Una generacion legitima con mas de 15 tecnologias se rechazaria.** → *Mitigacion*: no se ha observado ningun caso real que se acerque a ese numero; si ocurre, es una senal de que conviene agrupar tecnologias relacionadas en el enunciado en vez de subir el limite.
