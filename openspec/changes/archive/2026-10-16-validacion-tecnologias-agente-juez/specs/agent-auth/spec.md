# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Mecanismo de verificacion uniforme en los 5 agentes`
- TO: `### Requirement: Mecanismo de verificacion uniforme en todos los agentes`

## MODIFIED Requirements

### Requirement: Credencial de servicio obligatoria en toda peticion A2A
El sistema SHALL exigir una credencial de servicio valida en toda peticion A2A entrante a cualquiera de los agentes LLM (`code`, `evaluator`, `exercises`, `reviewer`, `validator`, `web`), verificada antes de que la peticion llegue a cualquier handler de negocio del agente.

#### Scenario: Peticion con credencial valida se procesa
- **WHEN** el backend envia una peticion A2A a un agente incluyendo la credencial de servicio vigente
- **THEN** el agente procesa la peticion con normalidad

#### Scenario: Peticion sin credencial se rechaza
- **WHEN** una peticion A2A llega a un agente sin la cabecera de credencial de servicio
- **THEN** el agente SHALL rechazarla con `401` sin ejecutar ninguna logica de negocio (sin invocar al LLM, sin leer GitHub, sin llamar a Tavily, sin tocar la base de datos)

#### Scenario: Peticion con credencial invalida se rechaza
- **WHEN** una peticion A2A llega a un agente con una credencial de servicio que no coincide con la configurada
- **THEN** el agente SHALL rechazarla con `401` sin ejecutar ninguna logica de negocio

### Requirement: Mecanismo de verificacion uniforme en todos los agentes
El sistema SHALL verificar la credencial de servicio con el mismo mecanismo (misma cabecera, mismo formato de error, mismo punto de ejecucion antes del handler) en todos los agentes LLM, incluido el validador, sin variantes por agente.

#### Scenario: Mismo formato de rechazo en cualquier agente
- **WHEN** se envia una peticion sin credencial o con credencial invalida a cualquiera de los agentes LLM
- **THEN** todos SHALL responder con el mismo codigo de estado y la misma forma de error, independientemente de a cual de ellos se haya llamado

### Requirement: El backend se autentica en toda llamada A2A
El sistema SHALL incluir la credencial de servicio en toda llamada A2A que el backend orquestador haga a cualquiera de los agentes LLM, tanto en el flujo de generacion de ejercicios (incluido el validador) como en el de evaluacion de respuestas.

#### Scenario: Llamada del backend a un agente de generacion incluye la credencial
- **WHEN** el orquestador de generacion de ejercicios llama al agente de codigo, al agente web o al agente de ejercicios
- **THEN** la peticion SHALL incluir la credencial de servicio configurada

#### Scenario: Llamada del backend al validador incluye la credencial
- **WHEN** el orquestador de generacion de ejercicios llama al agente validador antes que a los agentes de entrada
- **THEN** la peticion SHALL incluir la credencial de servicio configurada

#### Scenario: Llamada del backend a un agente de evaluacion incluye la credencial
- **WHEN** el orquestador de evaluacion de respuestas llama al agente evaluador o al agente revisor
- **THEN** la peticion SHALL incluir la credencial de servicio configurada
