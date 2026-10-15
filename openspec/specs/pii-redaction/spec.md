# pii-redaction Specification

## Purpose
Garantiza que un dato personal real (email, telefono, tarjeta, IP, IBAN, URL o nombre de persona) escrito dentro del contenido de una llamada de los 5 agentes se sustituye por un marcador generico antes de que la llamada salga hacia el proveedor del LLM, de forma independiente de la ocultacion de trazas que ya existe en Langfuse.

## Requirements

### Requirement: Redaccion automatica de PII antes de la llamada al proveedor
El sistema SHALL detectar y sustituir, en el input de toda llamada de los 5 agentes al proxy LiteLLM, cualquier email, telefono, numero de tarjeta, direccion IP, codigo IBAN, URL o nombre de persona detectable, por un marcador generico, antes de invocar al proveedor subyacente.

#### Scenario: Input sin datos personales
- **WHEN** cualquiera de los 5 agentes envia una llamada cuyo input no contiene ningun dato personal detectable
- **THEN** la llamada llega al proveedor sin modificar

#### Scenario: Input con un email o telefono real
- **WHEN** el input de una llamada contiene un email o un numero de telefono real
- **THEN** el sistema SHALL sustituirlo por su marcador generico correspondiente antes de que la llamada llegue al proveedor subyacente

### Requirement: Redaccion aplicada automaticamente a los 5 agentes
El sistema SHALL aplicar la redaccion de PII a toda llamada de los 5 agentes por igual, sin que ninguno tenga que solicitarla explicitamente ni requiera cambios en su codigo.

#### Scenario: Cualquier agente, sin configuracion adicional
- **WHEN** cualquiera de los 5 agentes realiza una llamada al proxy
- **THEN** la redaccion de PII se aplica sin que el agente haya pedido ningun guardrail en la llamada
