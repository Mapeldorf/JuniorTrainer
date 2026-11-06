# Tasks

## 1. Agente validador: ampliar el criterio del prompt

- [x] 1.1 Reescribir `_BASE_SYSTEM_PROMPT` en `agents/validator/app/service.py` para aceptar como tema valido (a) una tecnologia de programacion y (b) un concepto, caracteristica, modulo, API, patron o tema propio de una tecnologia o lenguaje, con ejemplos ("Componentes en Angular", "Hooks en React", "JOINs en SQL"), manteniendo la politica default-deny para datos personales, nombres y temas ajenos. Verificado en vivo contra LiteLLM: las 5 entradas tipo tema del catalogo dan `valid=True` y los controles ("cocina italiana", un nombre de persona) dan `valid=False`.
- [x] 1.2 Ajustar el wording de `_BASE_RESPONSE_FIELDS_PROMPT` (campos `valid` e `invalid_technologies`) para hablar de "tema valido para ejercicios de programacion", coherente con el criterio ampliado. Verificado leyendo el fichero.

## 2. Determinismo del veredicto

- [x] 2.1 Fijar `temperature=0` en `build_validator_model` (`agents/validator/app/llm.py`) para que el mismo input no de veredictos contradictorios entre llamadas (alta en catalogo vs. validacion de generacion). Verificado leyendo el fichero y con la recarga en caliente del agente (`WatchFiles detected changes in 'app/llm.py'. Reloading...`).

## 3. Verificacion

- [ ] 3.1 Ampliar `agents/validator/scripts/verify_validator.py` con al menos un caso de concepto/tema propio de una tecnologia que espera `valid=True` (p. ej. "Componentes en Angular") y un caso de control no-tecnologico que espera `valid=False`, en contexto `generation`. Verificar ejecutando el script contra LiteLLM de desarrollo.
- [ ] 3.2 Reproducir el caso original end-to-end: iniciar una generacion con "Componentes en Angular" y comprobar que supera la validacion y avanza a los agentes de entrada (`POST /generations` + `GET /generations/{id}` contra el docker-compose local).

## 4. Documentacion y specs

- [ ] 4.1 Revisar el comentario de modulo de `agents/validator/app/service.py` y `docs/especificacion-agentes.md` por si describen el criterio del validador como "solo tecnologias", y actualizarlo al criterio ampliado. Verificar leyendo los ficheros.
- [ ] 4.2 Validar el change (`openspec validate validador-acepta-temas-tecnologia --strict`) y corregir cualquier aviso antes de darlo por listo.

## Workflow follow-up

- Archivar el change y sincronizar `openspec/specs/technology-validation/spec.md` una vez implementado y revisado.
