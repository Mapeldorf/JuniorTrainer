# Spec Delta

## MODIFIED Requirements

### Requirement: Techo de gasto por key
El sistema SHALL asignar a cada una de las 6 virtual keys un `max_budget` configurable
por entorno con reseteo cada 30 dias (`budget_duration`), con un valor por defecto de
5 USD pensado para desarrollo, y SHALL bloquear cualquier llamada que supere ese
presupuesto hasta que el periodo se reinicie o el presupuesto se amplie manualmente.

#### Scenario: Llamada dentro de presupuesto
- **WHEN** una key con gasto acumulado por debajo de su `max_budget` llama a su modelo permitido
- **THEN** LiteLLM atiende la peticion con normalidad

#### Scenario: Llamada que supera el presupuesto
- **WHEN** una key cuyo gasto acumulado ya alcanzo su `max_budget` intenta llamar a cualquier modelo
- **THEN** LiteLLM SHALL rechazar la peticion sin invocar al proveedor subyacente, con un error que identifica que el motivo es presupuesto superado (no autenticacion ni restriccion de modelo)

### Requirement: Aprovisionamiento con budget desde la creacion
El sistema SHALL crear cada virtual key nueva ya con su `max_budget` y `budget_duration`
establecidos, sin requerir un paso de configuracion posterior, tomando el `max_budget`
de una variable de entorno con 5 USD por defecto, y SHALL rechazar un valor que no sea
un numero mayor que 0 sin crear ni modificar ninguna key.

#### Scenario: Aprovisionar una key nueva
- **WHEN** se ejecuta el script de aprovisionamiento para un agente que todavia no tiene virtual key y no se configura el importe del budget por entorno
- **THEN** la key creada tiene `max_budget=5` y `budget_duration=30d` desde el momento de su creacion

#### Scenario: Aprovisionar una key nueva con el importe de produccion
- **WHEN** se ejecuta el script de aprovisionamiento con la variable de entorno del budget puesta a 50
- **THEN** la key creada tiene `max_budget=50` y `budget_duration=30d` desde el momento de su creacion

#### Scenario: Importe de budget invalido
- **WHEN** se ejecuta el script con la variable de entorno del budget puesta a un valor que no es un numero mayor que 0
- **THEN** el script termina con un error que identifica la variable, sin crear ni modificar ninguna key

### Requirement: Keys existentes sin budget se actualizan, no se omiten
El sistema SHALL detectar, al re-ejecutar el aprovisionamiento, si una key ya existente
no tiene `max_budget` configurado, y en ese caso SHALL actualizarla con el `max_budget`
vigente (el de la variable de entorno, 5 USD por defecto) en vez de dejarla sin limite;
y SHALL no sobrescribir un `max_budget` que ya tuviera, aunque difiera del vigente.

#### Scenario: Re-ejecutar el aprovisionamiento sobre una key sin budget
- **WHEN** se ejecuta el script de aprovisionamiento y encuentra una key existente sin `max_budget`
- **THEN** el script actualiza esa key con el `max_budget` vigente y `budget_duration=30d`, sin generar una key nueva ni invalidar la existente

#### Scenario: Re-ejecutar el aprovisionamiento sobre una key que ya tiene budget
- **WHEN** se ejecuta el script de aprovisionamiento y encuentra una key existente que ya tiene `max_budget` configurado
- **THEN** el script la deja intacta, sin sobrescribir ese budget aunque el importe vigente sea distinto (por ejemplo, una key con 5 USD en un proxy donde ahora se configura 50)
