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

### Requirement: Bloqueo automatizado de prompt injection restringido al gate de entrada

El sistema SHALL ejecutar una comprobacion automatizada de prompt injection sobre el input de toda llamada del agente validador al proxy, tanto hacia su modelo principal como hacia su modelo de respaldo, antes de invocar al proveedor subyacente, y SHALL rechazar la llamada cuando detecte un intento. Los agentes evaluador y revisor quedan fuera de esta comprobacion en la postura vigente: su activacion esta gobernada por el requisito de recalibracion de esta misma especificacion.

#### Scenario: Input del validador sin intento de prompt injection

- **WHEN** el validador envia una llamada cuyo input no contiene ningun intento de prompt injection
- **THEN** la comprobacion lo deja pasar y la llamada al proveedor subyacente se realiza con normalidad

#### Scenario: Intento de prompt injection en el validador

- **WHEN** el input de una llamada del agente validador contiene un intento de prompt injection que el detector reconoce
- **THEN** la comprobacion SHALL bloquear la llamada y la generacion queda en estado de error

#### Scenario: La comprobacion cubre tambien el modelo de respaldo

- **WHEN** la llamada del validador se dirige a su modelo de respaldo tras un fallo del principal
- **THEN** la comprobacion se aplica igualmente antes de invocar al proveedor de respaldo

### Requirement: Reactivacion del bloqueo en evaluador y revisor supeditada a recalibracion

El sistema SHALL mantener desactivada la comprobacion automatizada de prompt injection sobre los deployments de los agentes evaluador y revisor, y SHALL activarla unicamente despues de una recalibracion documentada: subir el umbral de *enforcement* del detector y remedir la tasa de falsos positivos sobre el corpus de respuestas reales ya redactadas, de modo que la activacion no rechace contenido legitimo de alumnos.

#### Scenario: Configuracion vigente sin el bloqueo en evaluador y revisor

- **WHEN** el evaluador o el revisor envian una llamada al proxy
- **THEN** la llamada no pasa por la comprobacion automatizada, y la mitigacion aplicable al texto del alumno es la delimitacion como dato y la instruccion defensiva del prompt

#### Scenario: La medicion previa sigue mostrando falsos positivos

- **WHEN** la tasa de falsos positivos medida sobre el corpus de respuestas reales redactadas muestra que la activacion rechazaria contenido legitimo
- **THEN** el bloqueo no se activa en evaluador ni en revisor, y la decision queda documentada con la medicion

#### Scenario: Activacion tras la recalibracion

- **WHEN** el umbral de *enforcement* se ha subido y la remedicion sobre el mismo corpus ya no rechaza contenido legitimo
- **THEN** la activacion del bloqueo procede como change propio, con la verificacion de la configuracion sobre los deployments afectados

### Requirement: Material de redaccion tratado como dato en el agente de ejercicios

El agente de ejercicios SHALL insertar el resumen de documentacion y el resumen y los fragmentos de repositorio en el prompt del modelo siempre delimitados explicitamente como dato, y SHALL instruir al modelo para ignorar cualquier texto dentro de ese contenido que parezca dirigido a el.

#### Scenario: El resumen de documentacion deriva de una pagina con texto dirigido al modelo

- **WHEN** el resumen de documentacion que recibe el redactor deriva de contenido web que incluia una instruccion dirigida al modelo, y ese texto llega dentro del resumen
- **THEN** el modelo no cambia su comportamiento de redaccion por ese texto, y los candidatos se generan a partir del material como dato, no como instruccion

#### Scenario: Los fragmentos de repositorio contienen comentarios dirigidos al modelo

- **WHEN** el resumen o los fragmentos de repositorio que recibe el redactor incluyen un comentario que parece una instruccion para cambiar de tarea o de formato
- **THEN** el modelo la ignora y los candidatos respetan el contrato de salida y las restricciones del prompt del redactor

### Requirement: La ruta de generacion no pasa por la comprobacion automatizada
El sistema SHALL NOT ejecutar la comprobacion automatizada de prompt injection sobre las llamadas de los agentes web, de codigo y de ejercicios, cuyo contenido de entrada procede de terceros o de un repositorio y no de un autor con incentivo para manipular al modelo.

#### Scenario: Contenido benigno de repositorio
- **WHEN** el agente de codigo procesa contenido que un detector de prompt injection marcaria como falso positivo (p. ej. una ruta o un nombre de fichero que contiene la palabra "role")
- **THEN** ese contenido no pasa por la comprobacion automatizada y la tarea del agente continua con normalidad, sin que un falso positivo pueda interrumpirla

#### Scenario: Un intento de inyeccion desde un repositorio o una pagina web
- **WHEN** el contenido de un repositorio o de un resultado de busqueda contiene un intento de manipular al modelo
- **THEN** la mitigacion aplicable es la delimitacion de ese contenido como dato y la ausencia de herramientas de escritura en el agente, que acotan el efecto a la calidad del resultado
