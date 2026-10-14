# agent-auth Specification

## Purpose

Define como cada agente LLM del sistema verifica que una peticion A2A procede del backend orquestador antes de ejecutar cualquier logica de negocio, y como el backend se autentica frente a ellos.

## Requirements

### Requirement: Credencial de servicio obligatoria en toda peticion A2A
El sistema SHALL exigir una credencial de servicio valida en toda peticion A2A entrante a cualquiera de los agentes LLM (`code`, `evaluator`, `exercises`, `reviewer`, `web`), verificada antes de que la peticion llegue a cualquier handler de negocio del agente.

#### Scenario: Peticion con credencial valida se procesa
- **WHEN** el backend envia una peticion A2A a un agente incluyendo la credencial de servicio vigente
- **THEN** el agente procesa la peticion con normalidad

#### Scenario: Peticion sin credencial se rechaza
- **WHEN** una peticion A2A llega a un agente sin la cabecera de credencial de servicio
- **THEN** el agente SHALL rechazarla con `401` sin ejecutar ninguna logica de negocio (sin invocar al LLM, sin leer GitHub, sin llamar a Tavily, sin tocar la base de datos)

#### Scenario: Peticion con credencial invalida se rechaza
- **WHEN** una peticion A2A llega a un agente con una credencial de servicio que no coincide con la configurada
- **THEN** el agente SHALL rechazarla con `401` sin ejecutar ninguna logica de negocio

### Requirement: Mecanismo de verificacion uniforme en los 5 agentes
El sistema SHALL verificar la credencial de servicio con el mismo mecanismo (misma cabecera, mismo formato de error, mismo punto de ejecucion antes del handler) en los 5 agentes, sin variantes por agente.

#### Scenario: Mismo formato de rechazo en cualquier agente
- **WHEN** se envia una peticion sin credencial o con credencial invalida a cualquiera de los 5 agentes
- **THEN** todos SHALL responder con el mismo codigo de estado y la misma forma de error, independientemente de a cual de los 5 se haya llamado

### Requirement: Origen y proteccion de la credencial
El sistema SHALL cargar la credencial de servicio desde configuracion o un gestor de secretos, SHALL NOT dejarla hardcodeada en el codigo fuente, y SHALL NOT registrarla en claro en logs ni en trazas (Langfuse u otro backend de tracing).

#### Scenario: La credencial no aparece en logs
- **WHEN** un agente rechaza o acepta una peticion A2A
- **THEN** ningun log ni traza generado por esa peticion SHALL contener el valor literal de la credencial de servicio

### Requirement: El backend se autentica en toda llamada A2A
El sistema SHALL incluir la credencial de servicio en toda llamada A2A que el backend orquestador haga a cualquiera de los 5 agentes, tanto en el flujo de generacion de ejercicios como en el de evaluacion de respuestas.

#### Scenario: Llamada del backend a un agente de generacion incluye la credencial
- **WHEN** el orquestador de generacion de ejercicios llama al agente de codigo, al agente web o al agente de ejercicios
- **THEN** la peticion SHALL incluir la credencial de servicio configurada

#### Scenario: Llamada del backend a un agente de evaluacion incluye la credencial
- **WHEN** el orquestador de evaluacion de respuestas llama al agente evaluador o al agente revisor
- **THEN** la peticion SHALL incluir la credencial de servicio configurada

### Requirement: Compatibilidad con la trazabilidad existente
El sistema SHALL mantener el funcionamiento del `trace_id` propagado a Langfuse sin cambios al introducir la verificacion de credencial: la autenticacion de servicio SHALL actuar como una capa de transporte independiente de la trazabilidad.

#### Scenario: Una peticion autenticada conserva su trace_id
- **WHEN** el backend envia una peticion A2A con credencial de servicio valida y con `trace_id` en los metadatos del mensaje
- **THEN** el agente SHALL procesar la peticion y seguir propagando ese mismo `trace_id` a Langfuse como antes de este cambio
