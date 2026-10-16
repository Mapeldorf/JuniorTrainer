# Spec Delta

## MODIFIED Requirements

### Requirement: Deteccion automatizada de prompt injection en el proxy
El sistema SHALL ejecutar una comprobacion automatizada de prompt injection (Lakera Guard) sobre el input de toda llamada de los agentes al proxy LiteLLM, antes de invocar al proveedor subyacente, independientemente de si el agente la solicita explicitamente. Para los agentes web, de codigo, de ejercicios, evaluador y revisor, la comprobacion SHALL ser de solo observacion: SHALL registrar el resultado de la deteccion y SHALL NOT bloquear ni rechazar la llamada por ese resultado. Para el agente validador de tecnologias, la comprobacion SHALL bloquear la llamada cuando detecte un intento de prompt injection.

#### Scenario: Input sin intento de prompt injection
- **WHEN** un agente envia una llamada cuyo input no contiene ningun intento de prompt injection
- **THEN** la comprobacion lo deja pasar y la llamada al proveedor subyacente se realiza con normalidad

#### Scenario: Input con un intento de prompt injection detectable
- **WHEN** el input de una llamada de un agente de solo observacion contiene un intento de prompt injection que el detector reconoce
- **THEN** el sistema registra la deteccion y la llamada al proveedor subyacente se realiza igualmente, sin bloquearla

#### Scenario: Falso positivo sobre contenido benigno
- **WHEN** el detector marca como prompt injection contenido que no lo es (p. ej. una ruta o un nombre de fichero que contiene la palabra "role") en una llamada de un agente de solo observacion
- **THEN** la llamada no se bloquea y la tarea del agente continua con normalidad

#### Scenario: Input con un intento de prompt injection detectable en el validador
- **WHEN** el input de una llamada del agente validador contiene un intento de prompt injection que el detector reconoce
- **THEN** la comprobacion SHALL bloquear la llamada y la generacion queda en estado de error

#### Scenario: Input limpio en el validador
- **WHEN** el input de una llamada del agente validador no contiene ningun intento de prompt injection
- **THEN** la comprobacion lo deja pasar y la llamada al proveedor subyacente se realiza con normalidad
