# agent-resilience Specification

## Purpose

Define los limites de tiempo y de tasa que protegen a cada agente LLM frente a dependencias externas (LLM, Tavily) que se queden colgadas, y frente a un volumen de peticiones A2A por encima del uso legitimo esperado.

## Requirements

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

### Requirement: Timeout explicito en el proxy LiteLLM
El proxy LiteLLM SHALL fijar un timeout explicito para toda llamada que hace a un proveedor subyacente, independiente de cualquier timeout que los clientes (los agentes) configuren por su cuenta, de forma que una llamada colgada del lado del proveedor falle en un tiempo acotado sin depender de que el cliente la corte.

#### Scenario: El proveedor subyacente no responde
- **WHEN** una llamada de LiteLLM a un proveedor subyacente no recibe respuesta dentro del timeout configurado en el proxy
- **THEN** LiteLLM corta la llamada y devuelve un error de timeout al cliente, sin esperar mas alla de ese limite

#### Scenario: Una llamada normal no se ve afectada
- **WHEN** el proveedor subyacente responde dentro del tiempo habitual
- **THEN** la llamada se completa con normalidad, sin ningun cambio de comportamiento por este requisito

### Requirement: Fallback automatico a un proveedor alternativo
El proxy LiteLLM SHALL reintentar automaticamente, contra un modelo de un proveedor alternativo, toda llamada que falle al modelo logico principal, antes de devolver el error al agente que la origino.

#### Scenario: El modelo principal falla
- **WHEN** una llamada de LiteLLM al modelo principal de un modelo logico falla
- **THEN** LiteLLM SHALL reintentar la misma llamada contra el modelo de fallback configurado para ese modelo logico, sin que el agente tenga que solicitarlo

#### Scenario: El modelo principal responde con normalidad
- **WHEN** el modelo principal responde correctamente
- **THEN** la llamada se completa con normalidad, sin invocar al modelo de fallback

### Requirement: El fallback respeta la restriccion de modelo por virtual key
Una virtual key SOLO SHALL poder completar una llamada de fallback si el modelo de fallback correspondiente esta incluido en su lista de modelos permitidos.

#### Scenario: La virtual key tiene permitido su modelo de fallback
- **WHEN** la llamada de un agente a su modelo principal falla y LiteLLM reintenta contra el modelo de fallback que esa virtual key tiene permitido
- **THEN** la llamada de fallback se completa con normalidad

#### Scenario: Una virtual key no puede usar el fallback de otro agente
- **WHEN** se intenta usar una virtual key para llamar directamente al modelo de fallback de un modelo logico distinto del suyo
- **THEN** LiteLLM SHALL rechazar la llamada, igual que ya rechaza una llamada directa a cualquier otro modelo que esa key no tenga permitido
