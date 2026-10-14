# Spec Delta

## Purpose

Define que datos de los agentes nunca se registran en claro en el backend de tracing externo (Langfuse), con independencia de que la traza en si siga existiendo con el resto de su metadata (coste, latencia, tokens, modelo, exito/fallo).

## ADDED Requirements

### Requirement: Codigo de repositorio no se registra en claro en Langfuse
El sistema SHALL evitar que el contenido literal de ficheros de un repositorio llegue en claro al backend de tracing externo, en cualquier llamada al LLM donde ese contenido se interpole en el prompt o pueda aparecer en la respuesta, independientemente de en que agente ocurra esa llamada.

#### Scenario: Analisis del agente de codigo
- **WHEN** el agente de codigo llama al LLM para analizar el contenido de ficheros leidos de un repositorio
- **THEN** el prompt y la respuesta de esa llamada SHALL NOT aparecer en claro en el backend de tracing externo

#### Scenario: Redaccion de ejercicios con fragmentos de repositorio
- **WHEN** el agente de ejercicios llama al LLM con fragmentos de codigo de un repositorio recibidos de otro agente
- **THEN** el prompt y la respuesta de esa llamada SHALL NOT aparecer en claro en el backend de tracing externo

### Requirement: Respuesta de un alumno no se registra en claro en Langfuse
El sistema SHALL evitar que la respuesta literal de un alumno a un ejercicio llegue en claro al backend de tracing externo, en cualquier llamada al LLM donde esa respuesta se interpole en el prompt.

#### Scenario: Evaluacion de una respuesta
- **WHEN** el agente evaluador o el agente revisor llaman al LLM con la respuesta de un alumno en el prompt
- **THEN** el prompt de esa llamada SHALL NOT aparecer en claro en el backend de tracing externo

### Requirement: Contenido de busqueda web no se registra en claro en Langfuse
El sistema SHALL evitar que el contenido de busqueda web de terceros llegue en claro al backend de tracing externo, en la llamada al LLM donde ese contenido se interpola en el prompt.

#### Scenario: Resumen de busqueda web
- **WHEN** el agente web llama al LLM con fragmentos de resultados de busqueda en el prompt
- **THEN** el prompt de esa llamada SHALL NOT aparecer en claro en el backend de tracing externo

### Requirement: La redaccion no depende de que exista un trace_id
El sistema SHALL aplicar la redaccion de una llamada al LLM independientemente de si esa llamada lleva un `trace_id` de una tarea orquestada, de forma que una ejecucion en solitario (sin orquestador) no quede sin proteccion.

#### Scenario: Llamada sensible sin trace_id
- **WHEN** un agente hace una llamada al LLM que debe redactarse, sin ningun `trace_id` de orquestacion
- **THEN** el prompt y, si aplica, la respuesta de esa llamada SHALL NOT aparecer en claro en el backend de tracing externo

### Requirement: El resto de metadata de la traza se conserva
El sistema SHALL mantener visible en el backend de tracing externo el resto de metadata de una llamada redactada (coste, latencia, numero de tokens, modelo usado, si tuvo exito o fallo), de forma que la redaccion no elimine la observabilidad operativa de la traza.

#### Scenario: Traza redactada sigue siendo util para depurar costes/latencia
- **WHEN** se consulta en el backend de tracing externo una traza de una llamada redactada
- **THEN** el coste, la latencia, el numero de tokens, el modelo usado y si tuvo exito o fallo SHALL seguir siendo visibles, aunque el contenido del prompt/respuesta no lo sea
