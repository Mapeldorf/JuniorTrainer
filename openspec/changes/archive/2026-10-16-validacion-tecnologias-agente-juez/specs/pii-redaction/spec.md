# Spec Delta

## ADDED Requirements

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
