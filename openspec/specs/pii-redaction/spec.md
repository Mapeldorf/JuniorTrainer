# pii-redaction Specification

## Purpose
Garantiza que un dato personal real (email, telefono, tarjeta, IP o IBAN) escrito dentro del contenido de una llamada de los 5 agentes se sustituye por un marcador generico antes de que la llamada salga hacia el proveedor del LLM, de forma independiente de la ocultacion de trazas que ya existe en Langfuse. Las entidades `URL` y nombre de persona quedaron fuera (change `quitar-url-person-presidio`): disparaban falsos positivos masivos sobre rutas e identificadores de codigo y rompian la generacion de ejercicios. La redaccion se aplica solo al input: enmascarar tambien la respuesta del modelo corrompia el contenido generado sin aportar proteccion real (el proveedor ya vio el input).

## Requirements

### Requirement: Redaccion automatica de PII antes de la llamada al proveedor
El sistema SHALL detectar y sustituir, en el input de toda llamada de los 5 agentes al proxy LiteLLM, cualquier email, telefono, numero de tarjeta, direccion IP o codigo IBAN detectable, por un marcador generico, antes de invocar al proveedor subyacente.

#### Scenario: Input sin datos personales
- **WHEN** cualquiera de los 5 agentes envia una llamada cuyo input no contiene ningun dato personal detectable
- **THEN** la llamada llega al proveedor sin modificar

#### Scenario: Input con un email o telefono real
- **WHEN** el input de una llamada contiene un email o un numero de telefono real
- **THEN** el sistema SHALL sustituirlo por su marcador generico correspondiente antes de que la llamada llegue al proveedor subyacente

### Requirement: El output del modelo no se redacta
El sistema SHALL devolver la respuesta del modelo sin aplicar la redaccion de PII sobre ella: la redaccion solo actua sobre el input.

#### Scenario: Respuesta con texto que parece un dato personal
- **WHEN** el modelo devuelve contenido generado (p. ej. el texto de un ejercicio) que contiene un email, un telefono o cualquier texto detectable como entidad
- **THEN** el sistema SHALL devolverlo tal cual, sin sustituir nada por un marcador


### Requirement: Redaccion aplicada automaticamente a los 5 agentes
El sistema SHALL aplicar la redaccion de PII a toda llamada de los 5 agentes por igual, sin que ninguno tenga que solicitarla explicitamente ni requiera cambios en su codigo.

#### Scenario: Cualquier agente, sin configuracion adicional
- **WHEN** cualquiera de los 5 agentes realiza una llamada al proxy
- **THEN** la redaccion de PII se aplica sin que el agente haya pedido ningun guardrail en la llamada
