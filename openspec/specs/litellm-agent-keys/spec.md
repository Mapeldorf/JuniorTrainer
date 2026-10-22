# litellm-agent-keys Specification

## Purpose
Garantiza que cada agente LLM autentica frente al proxy de LiteLLM con una credencial propia, restringida al modelo logico que le corresponde, de forma que el uso y el coste sean atribuibles por agente y cualquiera de las 6 credenciales pueda revocarse sin afectar a los demas agentes.

## Requirements

### Requirement: Credencial propia por agente
El sistema SHALL asignar a cada uno de los 6 agentes (`web`, `code`, `exercises`, `evaluator`, `reviewer`, `validator`) una virtual key de LiteLLM distinta de las de los demas agentes, y ningun agente SHALL autenticar sus llamadas de negocio al proxy con la `master_key` de administracion.

#### Scenario: Cada agente usa su propia key
- **WHEN** cualquiera de los 6 agentes realiza una llamada al proxy de LiteLLM para su modelo logico
- **THEN** la llamada se autentica con la virtual key propia de ese agente, no con la de ningun otro agente ni con la `master_key`

### Requirement: Restriccion de modelo por key
El sistema SHALL restringir cada virtual key, en LiteLLM, al modelo logico que el agente correspondiente necesita llamar y a su deployment de fallback: la de `web`, `code` y `exercises` a `generator`; la de `evaluator` a `evaluator`; la de `reviewer` a `reviewer`; la de `validator` a `validator`.

#### Scenario: Una key solo puede llamar a su modelo permitido
- **WHEN** se usa la virtual key de un agente para llamar al modelo logico que tiene asignado
- **THEN** LiteLLM atiende la peticion con normalidad

#### Scenario: La lista de modelos permitidos incluye el deployment de fallback
- **WHEN** se aprovisiona o se actualiza la virtual key de un agente
- **THEN** su lista de modelos permitidos incluye tambien el deployment de fallback de su modelo logico, como exige el requisito "El fallback respeta la restriccion de modelo por virtual key" de `specs/agent-resilience/spec.md`

#### Scenario: Una key no puede llamar a un modelo que no le corresponde
- **WHEN** se usa la virtual key de un agente para llamar a un modelo logico distinto del que tiene asignado (p. ej. la key de `evaluator` contra el modelo `generator`)
- **THEN** LiteLLM SHALL rechazar la peticion sin invocar al proveedor subyacente

### Requirement: Revocacion independiente por agente
El sistema SHALL permitir revocar o rotar la virtual key de un agente sin afectar a la disponibilidad de las virtual keys de los otros 5 agentes.

#### Scenario: Revocar la key de un agente no afecta a los demas
- **WHEN** se revoca la virtual key de un agente en LiteLLM
- **THEN** los otros 5 agentes SHALL seguir pudiendo llamar a sus respectivos modelos con normalidad
- **AND** el agente cuya key se revoco SHALL recibir un error de autenticacion del proxy en su siguiente llamada

### Requirement: Uso atribuible por agente
El sistema SHALL registrar en LiteLLM el consumo (numero de llamadas, tokens, coste) de cada virtual key por separado, de forma que el uso de un agente se pueda consultar sin incluir el de los demas.

#### Scenario: Consulta de uso de un agente
- **WHEN** se consulta el uso asociado a la virtual key de un agente concreto
- **THEN** la respuesta refleja unicamente las llamadas hechas con esa key, no las de las demas virtual keys ni las de la `master_key`

### Requirement: Techo de gasto por key
El sistema SHALL asignar a cada una de las 6 virtual keys un `max_budget` de 5 USD con reseteo cada 30 dias (`budget_duration`), y SHALL bloquear cualquier llamada que supere ese presupuesto hasta que el periodo se reinicie o el presupuesto se amplie manualmente.

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

### Requirement: Resolucion de modelo logico aislada de la configuracion de LiteLLM
El sistema SHALL resolver, en cada uno de los 6 agentes, el nombre del modelo logico que envia a LiteLLM (`generator`, `evaluator`, `reviewer` o `validator`, segun corresponda) de forma fija, sin leerlo de ninguna variable de entorno que `infra/litellm/config.yaml` tambien use para resolver el proveedor real detras de ese modelo logico.

#### Scenario: El agente envia el alias logico, no el nombre de proveedor
- **WHEN** cualquiera de los 6 agentes construye una llamada al proxy de LiteLLM
- **THEN** el campo `model` de esa llamada es el alias logico fijo del agente (`generator`, `evaluator`, `reviewer` o `validator`)
- **AND** ese valor no cambia aunque la variable de entorno que LiteLLM usa para resolver el proveedor real (`GENERATOR_MODEL`/`EVALUATOR_MODEL`/`REVIEWER_MODEL`/`VALIDATOR_MODEL`) este presente en el entorno del agente

#### Scenario: La llamada respeta la restriccion de modelo de la virtual key
- **WHEN** un agente con una virtual key restringida a su modelo logico realiza una llamada real a LiteLLM
- **THEN** LiteLLM la atiende con normalidad (no la rechaza con `403 key_model_access_denied`)

### Requirement: Limite de ritmo por key
El sistema SHALL asignar a cada una de las 6 virtual keys un limite de 60 peticiones por minuto (`rpm_limit`), y SHALL rechazar cualquier peticion que supere ese ritmo sin invocar al proveedor subyacente.

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

### Requirement: Exclusion del guardarrail global en la key del validador
El sistema SHALL marcar la virtual key del agente `validator`, y solo esa, con la metadata `opted_out_global_guardrails: ["lakera-guard"]`. La exclusion SOLO SHALL afectar a guardarrailes globales (`default_on: true`); los vinculados al deployment SHALL seguir ejecutandose.

#### Scenario: La key del validador lleva la exclusion
- **WHEN** se ejecuta el script de aprovisionamiento para el agente `validator`
- **THEN** la key creada tiene la metadata `opted_out_global_guardrails: ["lakera-guard"]`
- **AND** los guardarrailes de bloqueo vinculados a los deployments `validator` y `validator-fallback-hf` siguen aplicandose a sus llamadas

#### Scenario: El guardarrail global no enmascara la PII antes del gate de bloqueo
- **WHEN** la entrada del validador contiene un dato personal y la llamada sale hacia el proveedor
- **THEN** el guardarrail global `lakera-guard` no la ha enmascarado previamente, de forma que `presidio-pii-block` ve el dato en claro y SHALL rechazar la llamada

#### Scenario: Re-ejecutar el aprovisionamiento sobre una key del validador sin la exclusion
- **WHEN** se ejecuta el script de aprovisionamiento y encuentra la key de `validator` sin la metadata `opted_out_global_guardrails`, o con un valor que no incluye `lakera-guard`
- **THEN** el script actualiza esa key con la metadata correspondiente, sin generar una key nueva ni invalidar la existente

#### Scenario: Las keys de los demas agentes no llevan la exclusion
- **WHEN** se ejecuta el script de aprovisionamiento para cualquier agente distinto de `validator`
- **THEN** la key correspondiente no lleva metadata de exclusion de guardarrailes globales, y el guardarrail global `lakera-guard` se aplica a sus llamadas
