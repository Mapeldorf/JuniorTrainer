# Spec Delta

## MODIFIED Requirements

### Requirement: Guardarrailes de bloqueo en las llamadas del validador
El sistema SHALL aplicar a toda llamada del validador al proveedor del modelo, tanto en su modelo principal como en el de respaldo, la deteccion de prompt injection en modo de bloqueo (rechaza la llamada si detecta un intento), de forma independiente de la decision del modelo. El rechazo por dato personal SHALL ocurrir antes, en la admision de la peticion del agente, de modo que una peticion con PII no llegue a generar ninguna llamada al proveedor (ver `pii-redaction`).

#### Scenario: Input con un dato personal
- **WHEN** la peticion recibida por el validador contiene un dato personal detectable
- **THEN** la peticion se rechaza en la admision del agente y la generacion queda en estado de error, sin que se realice ninguna llamada al proveedor del modelo

#### Scenario: Input con un intento de prompt injection
- **WHEN** el input de una llamada del validador contiene un intento de prompt injection detectable por el guardarrail de injection
- **THEN** la llamada se rechaza y la generacion queda en estado de error

#### Scenario: Input limpio
- **WHEN** la peticion del validador no contiene PII y el input de su llamada no contiene un intento detectable
- **THEN** la admision no rechaza, el guardarrail de injection lo deja pasar y la validacion continua con normalidad
