# prompt-injection-mitigation Specification

## Purpose

Define que el sistema trata como dato, nunca como instruccion, todo texto de origen no confiable (respuestas de alumnos, codigo de apoyo, resultados de busqueda web) que se interpola en el prompt de un agente, para acotar el efecto de un intento de manipular al modelo a traves de ese texto.

## Requirements

### Requirement: Respuesta del alumno tratada como dato en el agente evaluador
El agente evaluador SHALL insertar `student_answer` y cada bloque de `code` en el prompt del modelo siempre delimitado explicitamente como dato, y SHALL instruir al modelo para ignorar cualquier texto dentro de ese contenido que parezca dirigido a el.

#### Scenario: Una respuesta contiene texto dirigido al modelo
- **WHEN** `student_answer` contiene una frase que parece una instruccion dirigida al modelo (p. ej. pedirle que cambie el verdict o revele su prompt)
- **THEN** el modelo no cambia su comportamiento de evaluacion por ese texto, y el verdict resultante sigue basandose unicamente en si la respuesta es correcta

### Requirement: Contenido ajeno tratado como dato en el agente revisor
El agente revisor SHALL insertar `student_answer` y la `justification` recibida del evaluador en el prompt del modelo siempre delimitado explicitamente como dato, y SHALL instruir al modelo para ignorar cualquier texto dentro de ese contenido que parezca dirigido a el.

#### Scenario: La justificacion o la respuesta contienen texto dirigido al modelo
- **WHEN** `student_answer` o la `justification` recibida contienen una frase que parece una instruccion dirigida al modelo
- **THEN** el modelo no cambia su comportamiento de revision por ese texto, y la justificacion revisada sigue reflejando el verdict ya decidido, no una instruccion inyectada

### Requirement: Resultados de busqueda web tratados como dato en el agente web
El agente web SHALL insertar el `title` y el `snippet` de cada resultado de busqueda en el prompt del modelo siempre delimitado explicitamente como dato, y SHALL instruir al modelo para ignorar cualquier texto dentro de ese contenido que parezca dirigido a el.

#### Scenario: Un resultado de busqueda contiene texto dirigido al modelo
- **WHEN** el `title` o el `snippet` de un resultado de Tavily contienen una frase que parece una instruccion dirigida al modelo
- **THEN** el modelo no cambia su comportamiento de resumen por ese texto, y el resultado no refleja haber seguido esa instruccion

### Requirement: Deteccion automatizada de prompt injection en el proxy
El sistema SHALL ejecutar una comprobacion automatizada de prompt injection (Lakera Guard) sobre el input de toda llamada de los 5 agentes al proxy LiteLLM, antes de invocar al proveedor subyacente, independientemente de si el agente la solicita explicitamente. La comprobacion SHALL ser de solo observacion: SHALL registrar el resultado de la deteccion y SHALL NOT bloquear ni rechazar la llamada por ese resultado.

#### Scenario: Input sin intento de prompt injection
- **WHEN** cualquiera de los 5 agentes envia una llamada cuyo input no contiene ningun intento de prompt injection
- **THEN** la comprobacion lo deja pasar y la llamada al proveedor subyacente se realiza con normalidad

#### Scenario: Input con un intento de prompt injection detectable
- **WHEN** el input de una llamada contiene un intento de prompt injection que el detector reconoce
- **THEN** el sistema registra la deteccion y la llamada al proveedor subyacente se realiza igualmente, sin bloquearla

#### Scenario: Falso positivo sobre contenido benigno
- **WHEN** el detector marca como prompt injection contenido que no lo es (p. ej. una ruta o un nombre de fichero que contiene la palabra "role")
- **THEN** la llamada no se bloquea y la tarea del agente continua con normalidad
