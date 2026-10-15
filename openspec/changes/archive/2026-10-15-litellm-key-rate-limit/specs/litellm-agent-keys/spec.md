# Spec Delta

## ADDED Requirements

### Requirement: Limite de ritmo por key
El sistema SHALL asignar a cada una de las 5 virtual keys un limite de 60 peticiones por minuto (`rpm_limit`), y SHALL rechazar cualquier peticion que supere ese ritmo sin invocar al proveedor subyacente.

#### Scenario: Peticiones dentro del limite
- **WHEN** una key realiza peticiones por debajo de su `rpm_limit` en la ventana de un minuto
- **THEN** LiteLLM las atiende con normalidad

#### Scenario: Peticiones por encima del limite
- **WHEN** una key supera su `rpm_limit` en la ventana de un minuto
- **THEN** LiteLLM SHALL rechazar el exceso con un error de limite de ritmo, sin invocar al proveedor subyacente

### Requirement: Aprovisionamiento y upsert del limite de ritmo
El sistema SHALL crear cada virtual key nueva con su `rpm_limit` ya establecido, y SHALL actualizar con ese mismo limite cualquier key existente que no lo tenga, sin regenerarla ni sobrescribir un limite distinto que ya tuviera.

#### Scenario: Aprovisionar una key nueva
- **WHEN** se ejecuta el script de aprovisionamiento para un agente que todavia no tiene virtual key
- **THEN** la key creada tiene `rpm_limit=60` desde el momento de su creacion

#### Scenario: Re-ejecutar el aprovisionamiento sobre una key sin limite de ritmo
- **WHEN** se ejecuta el script de aprovisionamiento y encuentra una key existente sin `rpm_limit`
- **THEN** el script actualiza esa key con `rpm_limit=60`, sin generar una key nueva ni invalidar la existente
