# Spec Delta

## ADDED Requirements

### Requirement: Deteccion automatizada de prompt injection en el proxy
El sistema SHALL ejecutar una comprobacion automatizada de prompt injection (Lakera Guard) sobre el input de toda llamada de los 5 agentes al proxy LiteLLM, antes de invocar al proveedor subyacente, independientemente de si el agente la solicita explicitamente.

#### Scenario: Input sin intento de prompt injection
- **WHEN** cualquiera de los 5 agentes envia una llamada cuyo input no contiene ningun intento de prompt injection
- **THEN** la comprobacion lo deja pasar y la llamada al proveedor subyacente se realiza con normalidad

#### Scenario: Input con un intento de prompt injection detectable
- **WHEN** el input de una llamada contiene un intento de prompt injection que el detector reconoce
- **THEN** el sistema SHALL rechazar la llamada antes de invocar al proveedor subyacente, sin gastar presupuesto de la virtual key del agente en esa llamada
