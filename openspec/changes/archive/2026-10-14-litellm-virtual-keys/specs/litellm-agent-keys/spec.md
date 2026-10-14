# Spec Delta

## Purpose

Garantiza que cada agente LLM autentica frente al proxy de LiteLLM con una credencial propia, restringida al modelo logico que le corresponde, de forma que el uso y el coste sean atribuibles por agente y cualquiera de las 5 credenciales pueda revocarse sin afectar a los demas agentes.

## ADDED Requirements

### Requirement: Credencial propia por agente
El sistema SHALL asignar a cada uno de los 5 agentes (`web`, `code`, `exercises`, `evaluator`, `reviewer`) una virtual key de LiteLLM distinta de las de los demas agentes, y ningun agente SHALL autenticar sus llamadas de negocio al proxy con la `master_key` de administracion.

#### Scenario: Cada agente usa su propia key
- **WHEN** cualquiera de los 5 agentes realiza una llamada al proxy de LiteLLM para su modelo logico
- **THEN** la llamada se autentica con la virtual key propia de ese agente, no con la de ningun otro agente ni con la `master_key`

### Requirement: Restriccion de modelo por key
El sistema SHALL restringir cada virtual key, en LiteLLM, a los modelos logicos que el agente correspondiente necesita llamar: la de `web`, `code` y `exercises` solo al modelo `generator`; la de `evaluator` solo a `evaluator`; la de `reviewer` solo a `reviewer`.

#### Scenario: Una key solo puede llamar a su modelo permitido
- **WHEN** se usa la virtual key de un agente para llamar al modelo logico que tiene asignado
- **THEN** LiteLLM atiende la peticion con normalidad

#### Scenario: Una key no puede llamar a un modelo que no le corresponde
- **WHEN** se usa la virtual key de un agente para llamar a un modelo logico distinto del que tiene asignado (p. ej. la key de `evaluator` contra el modelo `generator`)
- **THEN** LiteLLM SHALL rechazar la peticion sin invocar al proveedor subyacente

### Requirement: Revocacion independiente por agente
El sistema SHALL permitir revocar o rotar la virtual key de un agente sin afectar a la disponibilidad de las virtual keys de los otros 4 agentes.

#### Scenario: Revocar la key de un agente no afecta a los demas
- **WHEN** se revoca la virtual key de un agente en LiteLLM
- **THEN** los otros 4 agentes SHALL seguir pudiendo llamar a sus respectivos modelos con normalidad
- **AND** el agente cuya key se revoco SHALL recibir un error de autenticacion del proxy en su siguiente llamada

### Requirement: Uso atribuible por agente
El sistema SHALL registrar en LiteLLM el consumo (numero de llamadas, tokens, coste) de cada virtual key por separado, de forma que el uso de un agente se pueda consultar sin incluir el de los demas.

#### Scenario: Consulta de uso de un agente
- **WHEN** se consulta el uso asociado a la virtual key de un agente concreto
- **THEN** la respuesta refleja unicamente las llamadas hechas con esa key, no las de las demas virtual keys ni las de la `master_key`
