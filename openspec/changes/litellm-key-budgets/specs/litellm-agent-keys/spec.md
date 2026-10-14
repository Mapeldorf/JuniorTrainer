# Spec Delta

## ADDED Requirements

### Requirement: Techo de gasto por key
El sistema SHALL asignar a cada una de las 5 virtual keys un `max_budget` de 5 USD con reseteo cada 30 dias (`budget_duration`), y SHALL bloquear cualquier llamada que supere ese presupuesto hasta que el periodo se reinicie o el presupuesto se amplie manualmente.

#### Scenario: Llamada dentro de presupuesto
- **WHEN** una key con gasto acumulado por debajo de su `max_budget` llama a su modelo permitido
- **THEN** LiteLLM atiende la peticion con normalidad

#### Scenario: Llamada que supera el presupuesto
- **WHEN** una key cuyo gasto acumulado ya alcanzo su `max_budget` intenta llamar a cualquier modelo
- **THEN** LiteLLM SHALL rechazar la peticion sin invocar al proveedor subyacente, con un error que identifica que el motivo es presupuesto superado (no autenticacion ni restriccion de modelo)

### Requirement: Aprovisionamiento con budget desde la creacion
El sistema SHALL crear cada virtual key nueva ya con su `max_budget` y `budget_duration` establecidos, sin requerir un paso de configuracion posterior.

#### Scenario: Aprovisionar una key nueva
- **WHEN** se ejecuta el script de aprovisionamiento para un agente que todavia no tiene virtual key
- **THEN** la key creada tiene `max_budget=5` y `budget_duration=30d` desde el momento de su creacion

### Requirement: Keys existentes sin budget se actualizan, no se omiten
El sistema SHALL detectar, al re-ejecutar el aprovisionamiento, si una key ya existente no tiene `max_budget` configurado, y en ese caso SHALL actualizarla con el budget correspondiente en vez de dejarla sin limite.

#### Scenario: Re-ejecutar el aprovisionamiento sobre una key sin budget
- **WHEN** se ejecuta el script de aprovisionamiento y encuentra una key existente sin `max_budget`
- **THEN** el script actualiza esa key con `max_budget=5` y `budget_duration=30d`, sin generar una key nueva ni invalidar la existente

#### Scenario: Re-ejecutar el aprovisionamiento sobre una key que ya tiene budget
- **WHEN** se ejecuta el script de aprovisionamiento y encuentra una key existente que ya tiene `max_budget` configurado
- **THEN** el script la deja intacta, sin sobrescribir un budget que pudiera haberse ajustado manualmente despues de crearla
