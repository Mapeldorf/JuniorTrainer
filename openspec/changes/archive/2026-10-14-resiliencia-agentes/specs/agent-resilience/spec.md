# Spec Delta

## Purpose

Define los limites de tiempo y de tasa que protegen a cada agente LLM frente a dependencias externas (LLM, Tavily) que se queden colgadas, y frente a un volumen de peticiones A2A por encima del uso legitimo esperado.

## ADDED Requirements

### Requirement: Timeout explicito en las llamadas al LLM
Todo agente SHALL fijar un timeout explicito en su cliente del LLM, sin depender del valor por defecto de la libreria HTTP subyacente, de forma que una llamada colgada falle en un tiempo acotado en vez de bloquear la tarea indefinidamente.

#### Scenario: El proxy LiteLLM no responde
- **WHEN** una llamada de un agente al LLM no recibe respuesta dentro del timeout configurado
- **THEN** la llamada falla con un error de timeout, sin esperar mas alla de ese limite

#### Scenario: Una llamada normal no se ve afectada
- **WHEN** el LLM responde dentro del tiempo habitual
- **THEN** la tarea continua con normalidad, sin ningun cambio de comportamiento por este requisito

### Requirement: Timeout explicito en las llamadas a Tavily
El agente web SHALL fijar un timeout explicito en su cliente de busqueda Tavily, sin depender del valor por defecto de la libreria HTTP subyacente.

#### Scenario: Tavily no responde
- **WHEN** una busqueda a Tavily no recibe respuesta dentro del timeout configurado
- **THEN** la busqueda falla con un error de timeout, sin esperar mas alla de ese limite

### Requirement: Limite de peticiones por IP en cada agente
Todo agente SHALL limitar el numero de peticiones HTTP que acepta por IP en una ventana de tiempo, independientemente de si la credencial de servicio es valida, rechazando el exceso con un error claro sin ejecutar ninguna logica de negocio.

#### Scenario: Peticiones dentro del limite se procesan con normalidad
- **WHEN** una IP envia peticiones a un agente por debajo del limite configurado en la ventana de tiempo
- **THEN** el agente las procesa con normalidad

#### Scenario: Peticiones por encima del limite se rechazan
- **WHEN** una IP supera el limite de peticiones configurado en la ventana de tiempo, con credencial de servicio valida o no
- **THEN** el agente rechaza el exceso con un error de limite de tasa, sin invocar al LLM, a Tavily, a GitHub ni a la base de datos para esas peticiones
