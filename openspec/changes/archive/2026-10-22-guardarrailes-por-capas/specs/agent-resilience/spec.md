# Spec Delta

## ADDED Requirements

### Requirement: Cobertura de guardarrailes en los deployments de fallback
Todo deployment de fallback SHALL llevar vinculados al menos los mismos guardarrailes que su deployment primario, de forma que una llamada que se desvia al proveedor de respaldo no pierda ninguna de las protecciones que tendria contra el principal.

#### Scenario: El fallback conserva las protecciones del primario
- **WHEN** la llamada de un agente a su modelo principal falla y el sistema la reintenta contra su modelo de respaldo
- **THEN** los guardarrailes que se habrian aplicado contra el modelo principal se aplican igualmente contra el de respaldo

#### Scenario: Un fallback con menos guardarrailes que su primario
- **WHEN** la configuracion vincula a un deployment primario un guardarrail que su deployment de fallback no lleva
- **THEN** esa configuracion SHALL considerarse invalida

### Requirement: Verificacion estatica de la cobertura de guardarrailes
El sistema SHALL verificar la cobertura de guardarrailes de forma estatica a partir de la configuracion del proxy, sin necesidad de red, de modelo ni de credenciales, de modo que la comprobacion pueda ejecutarse en integracion continua en cada cambio.

#### Scenario: Configuracion coherente
- **WHEN** se verifica una configuracion en la que todo fallback cubre los guardarrailes de su primario y existe una redaccion de PII activa de forma global
- **THEN** la verificacion pasa

#### Scenario: Configuracion con un fallback descubierto
- **WHEN** se verifica una configuracion en la que un deployment de fallback no lleva un guardarrail que su primario si lleva
- **THEN** la verificacion SHALL fallar identificando el deployment y el guardarrail que falta

#### Scenario: Configuracion sin red de seguridad de redaccion
- **WHEN** se verifica una configuracion en la que ningun guardarrail de redaccion de PII esta activo de forma global
- **THEN** la verificacion SHALL fallar
