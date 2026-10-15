# Spec Delta

## MODIFIED Requirements

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
