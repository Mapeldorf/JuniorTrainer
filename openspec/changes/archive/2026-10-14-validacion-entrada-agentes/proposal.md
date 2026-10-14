# Proposal

## Why

Dos vacios de validacion determinista distintos, encontrados auditando `agents/code` y `agents/web`:

1. **`agents/code` no valida `owner`/`repo` por su cuenta.** `agents/code/app/github_ref.py` tiene una copia de `validate_owner_or_repo` (la misma regex anti path-traversal/SSRF que ya exige `specs/github-repo-access/spec.md`, requisito "Referencia de entrada del repositorio"), pero nunca se invoca: `agents/code/app/input.py` asume explicitamente que el backend ya valido esos valores (y, en efecto, `backend/app/schemas/generation.py` los valida con un `field_validator` de Pydantic antes de crear la generacion). El agente ahora exige autenticacion de servicio (change `autenticacion-backend-agentes`), pero sigue sin la segunda capa de defensa que el propio proyecto ya aplica en otros sitios: el agente de ejercicios revalida `count` 1-5 (`agents/exercises/app/input.py:45`) aunque el backend ya lo acota, precisamente para no depender solo del llamador.

2. **Ni el backend ni `agents/web` acotan el numero ni la longitud de las tecnologias de una generacion.** `StartGenerationRequest.technologies` (`backend/app/schemas/generation.py:25`) solo exige `min_length=1` -- sin maximo de elementos ni de longitud por elemento -- y `agents/web/app/input.py::parse_technologies` tampoco acota nada. Cada tecnologia se usa tal cual como query de Tavily y se interpola en el prompt del LLM, asi que una lista arbitrariamente larga (o una cadena arbitrariamente larga dentro de ella) es una via de coste sin limite en Tavily y en tokens de LLM, sin que ningun componente la rechace.

En ambos casos el patron correcto ya existe en el proyecto (el agente de ejercicios revalida `count`, el backend valida `owner`/`repo`); este change extiende ese mismo patron a los dos puntos que quedaron sin cubrir.

## What Changes

- `agents/code`: `analyze_repo` (o `input.py`) valida `owner` y `repo` con la misma regla de `github_ref.py` antes de usarlos en cualquier llamada a la API de GitHub, rechazando la tarea con un error claro si no cumplen el formato -- defensa en profundidad, no sustituye la validacion ya existente en el backend.
- `backend`: `StartGenerationRequest.technologies` pasa a exigir tambien un maximo de elementos y una longitud maxima por elemento (limites concretos a fijar en design.md).
- `agents/web`: `parse_technologies` revalida esos mismos limites (maximo de elementos y longitud maxima por elemento) antes de usarlos en Tavily o en el prompt del LLM, con el mismo criterio "revalidar lo que el backend ya valido" que ya usa el agente de ejercicios con `count`.

Fuera de alcance: el filtrado de `path` dentro de un repositorio ya autorizado (ya cubierto por el change `validar-path-agente-codigo`, archivado).

## Capabilities

### New Capabilities
(ninguna)

### Modified Capabilities
- `github-repo-access`: nuevo requisito de defensa en profundidad -- el agente de codigo SHALL validar `owner`/`repo` por su cuenta antes de construir cualquier URL de la API de GitHub, con independencia de que el backend ya los haya validado.
- `exercise-generation`: nuevo requisito de limite de tecnologias -- el sistema SHALL acotar el numero de tecnologias de una generacion y la longitud de cada una, tanto en la validacion de entrada del backend como en el agente web que las consume.

## Impact

- **Codigo afectado**: `agents/code/app/input.py`/`agents/code/app/service.py` (validar `owner`/`repo`), `backend/app/schemas/generation.py` (limites en `technologies`), `agents/web/app/input.py` (revalidar esos mismos limites).
- **Sin cambios**: `agents/code/app/github_ref.py` (la funcion de validacion ya existe, solo falta invocarla), `agents/exercises` (ya tiene su propio patron de revalidacion, sirve de referencia).
- **Compatibilidad**: una generacion con mas tecnologias (o tecnologias mas largas) que el limite elegido, que antes se aceptaba, pasa a rechazarse con un error de validacion (`422` en el backend). No hay otra ruptura de compatibilidad.
