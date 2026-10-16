# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Redaccion aplicada automaticamente a los 5 agentes`
- TO: `### Requirement: Redaccion aplicada automaticamente a las llamadas con texto del alumno`

## MODIFIED Requirements

### Requirement: Redaccion automatica de PII antes de la llamada al proveedor
El sistema SHALL detectar y sustituir, en el input de toda llamada del agente evaluador y del agente revisor al proxy LiteLLM, cualquier email, telefono, numero de tarjeta, direccion IP o codigo IBAN detectable, por un marcador generico, antes de invocar al proveedor subyacente.

#### Scenario: Input sin datos personales
- **WHEN** el evaluador o el revisor envia una llamada cuyo input no contiene ningun dato personal detectable
- **THEN** la llamada llega al proveedor sin modificar

#### Scenario: Input con un email o telefono real
- **WHEN** el input de una llamada del evaluador o del revisor contiene un email o un numero de telefono real
- **THEN** el sistema SHALL sustituirlo por su marcador generico correspondiente antes de que la llamada llegue al proveedor subyacente

### Requirement: Redaccion aplicada automaticamente a las llamadas con texto del alumno
El sistema SHALL aplicar la redaccion de PII a las llamadas del agente evaluador y del agente revisor, que son las que llevan el texto escrito por el alumno, sin que ningun agente tenga que solicitarla explicitamente ni requiera cambios en su codigo. El sistema SHALL NOT aplicar la redaccion de PII a las llamadas de los agentes web, de codigo y de ejercicios, cuyo input es contenido de terceros, de repositorio o derivado, no texto del alumno.

#### Scenario: Cualquier agente, sin configuracion adicional
- **WHEN** el evaluador o el revisor realiza una llamada al proxy
- **THEN** la redaccion de PII se aplica a esa llamada sin que el agente haya pedido ningun guardrail

#### Scenario: Llamada sin texto del alumno
- **WHEN** el agente web, el de codigo o el de ejercicios realiza una llamada al proxy
- **THEN** la redaccion de PII no se aplica: el input llega al proveedor tal cual
