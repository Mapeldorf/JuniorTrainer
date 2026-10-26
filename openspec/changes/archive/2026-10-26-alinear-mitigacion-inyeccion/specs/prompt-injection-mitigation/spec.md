# Spec Delta

## RENAMED Requirements

- FROM: `Bloqueo automatizado de prompt injection donde el autor tiene incentivo adverso`
- TO: `Bloqueo automatizado de prompt injection restringido al gate de entrada`

## MODIFIED Requirements

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

## ADDED Requirements

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