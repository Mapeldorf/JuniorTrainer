# Spec Delta

## ADDED Requirements

### Requirement: Limite de tecnologias por generacion
El sistema SHALL acotar una generacion a un numero maximo de tecnologias y a una longitud maxima por tecnologia (limites concretos en design.md), aplicado tanto al validar la peticion de inicio de la generacion como dentro del agente web antes de usarlas en una busqueda o en un prompt.

#### Scenario: Una generacion dentro de los limites se acepta
- **WHEN** se inicia una generacion con un numero de tecnologias y una longitud por tecnologia dentro de los limites configurados
- **THEN** el sistema acepta la peticion con normalidad

#### Scenario: Demasiadas tecnologias se rechaza al iniciar la generacion
- **WHEN** se inicia una generacion con mas tecnologias que el maximo permitido
- **THEN** el sistema SHALL rechazar la peticion con un error de validacion, sin crear ninguna fila de generacion ni invocar a ningun agente

#### Scenario: Una tecnologia demasiado larga se rechaza al iniciar la generacion
- **WHEN** se inicia una generacion con una tecnologia cuya longitud supera el maximo permitido
- **THEN** el sistema SHALL rechazar la peticion con un error de validacion, sin crear ninguna fila de generacion ni invocar a ningun agente

#### Scenario: El agente web revalida el limite con independencia del backend
- **WHEN** el agente web recibe una tarea con mas tecnologias que el maximo permitido, o con una tecnologia que supera la longitud maxima, sin pasar por la validacion del backend
- **THEN** el agente web SHALL rechazar la tarea con un error claro, sin llamar a Tavily ni al LLM con esa entrada
