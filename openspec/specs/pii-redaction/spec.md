# pii-redaction Specification

## Purpose
Garantiza que un dato personal real (email, telefono, tarjeta, IP o IBAN) escrito dentro del contenido de una llamada del agente evaluador o del agente revisor (las que llevan texto del alumno) se sustituye por un marcador generico antes de que la llamada salga hacia el proveedor del LLM, de forma independiente de la ocultacion de trazas que ya existe en Langfuse. Las entidades `URL` y nombre de persona quedaron fuera (change `quitar-url-person-presidio`): disparaban falsos positivos masivos sobre rutas e identificadores de codigo y rompian la generacion de ejercicios. La redaccion se aplica solo al input: enmascarar tambien la respuesta del modelo corrompia el contenido generado sin aportar proteccion real (el proveedor ya vio el input). Los agentes web, de codigo y de ejercicios quedan fuera (change `presidio-solo-evaluador-revisor`): su input es contenido de terceros, de repositorio o derivado, no texto del alumno.

## Requirements

### Requirement: Redaccion automatica de PII antes de la llamada al proveedor
El sistema SHALL detectar y sustituir, en el input de toda llamada del agente evaluador y del agente revisor al proxy LiteLLM, cualquier email, telefono, numero de tarjeta, direccion IP o codigo IBAN detectable, por un marcador generico, antes de invocar al proveedor subyacente.

#### Scenario: Input sin datos personales
- **WHEN** el evaluador o el revisor envia una llamada cuyo input no contiene ningun dato personal detectable
- **THEN** la llamada llega al proveedor sin modificar

#### Scenario: Input con un email o telefono real
- **WHEN** el input de una llamada del evaluador o del revisor contiene un email o un numero de telefono real
- **THEN** el sistema SHALL sustituirlo por su marcador generico correspondiente antes de que la llamada llegue al proveedor subyacente

### Requirement: El output del modelo no se redacta
El sistema SHALL devolver la respuesta del modelo sin aplicar la redaccion de PII sobre ella: la redaccion solo actua sobre el input.

#### Scenario: Respuesta con texto que parece un dato personal
- **WHEN** el modelo devuelve contenido generado (p. ej. el texto de un ejercicio) que contiene un email, un telefono o cualquier texto detectable como entidad
- **THEN** el sistema SHALL devolverlo tal cual, sin sustituir nada por un marcador

### Requirement: Redaccion aplicada automaticamente a las llamadas con texto del alumno
El sistema SHALL aplicar la redaccion de PII a las llamadas del agente evaluador y del agente revisor, que son las que llevan el texto escrito por el alumno, sin que ningun agente tenga que solicitarla explicitamente ni requiera cambios en su codigo. El sistema SHALL NOT aplicar la redaccion de PII a las llamadas de los agentes web, de codigo y de ejercicios, cuyo input es contenido de terceros, de repositorio o derivado, no texto del alumno.

#### Scenario: Cualquier agente, sin configuracion adicional
- **WHEN** el evaluador o el revisor realiza una llamada al proxy
- **THEN** la redaccion de PII se aplica a esa llamada sin que el agente haya pedido ningun guardrail

#### Scenario: Llamada sin texto del alumno
- **WHEN** el agente web, el de codigo o el de ejercicios realiza una llamada al proxy
- **THEN** la redaccion de PII no se aplica: el input llega al proveedor tal cual

### Requirement: Deteccion de PII en modo de bloqueo en el validador
El sistema SHALL ejecutar la deteccion de PII sobre el input de toda llamada del agente validador de tecnologias al proveedor del modelo, tanto en su modelo principal como en el de respaldo, y SHALL rechazar la llamada cuando detecte un email, telefono, numero de tarjeta, direccion IP o codigo IBAN, en lugar de sustituirlo por un marcador y continuar.

#### Scenario: Input del validador con un dato personal
- **WHEN** el input de una llamada del validador contiene un dato personal detectable (email, telefono, tarjeta, IP o IBAN)
- **THEN** el sistema rechaza la llamada y la generacion queda en estado de error, sin que el modelo llegue a procesar ese input

#### Scenario: Input del validador sin datos personales
- **WHEN** el input de una llamada del validador no contiene ningun dato personal detectable
- **THEN** la llamada llega al proveedor sin modificar y la validacion continua con normalidad

#### Scenario: Los demas agentes no se ven afectados
- **WHEN** el agente evaluador o el agente revisor realizan una llamada al proveedor
- **THEN** la deteccion de PII sigue sustituyendo el dato por su marcador y continuando (no bloquea), y los agentes web, de codigo y de ejercicios siguen sin aplicar la redaccion
