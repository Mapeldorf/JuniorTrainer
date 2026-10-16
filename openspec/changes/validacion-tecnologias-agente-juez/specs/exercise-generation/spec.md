# Spec Delta

## MODIFIED Requirements

### Requirement: Orquestacion en paralelo de los agentes de entrada
El sistema SHALL lanzar el agente web y, si hay repositorio, el agente de codigo en paralelo, despues de que el agente validador haya dado un veredicto afirmativo sobre las tecnologias, SHALL esperar a que ambos terminen, y SHALL enviar sus resultados junto con el tipo de ejercicio y el numero pedido al agente de ejercicios.

#### Scenario: Generacion con repositorio
- **WHEN** una generacion incluye repositorio
- **THEN** el agente web y el agente de codigo se ejecutan a la vez, y el agente de ejercicios solo recibe el mensaje despues de que ambos han terminado

#### Scenario: Generacion sin repositorio
- **WHEN** una generacion no incluye repositorio
- **THEN** el agente de codigo no se ejecuta, y el agente de ejercicios recibe solo el resultado del agente web

#### Scenario: Validacion previa a los agentes de entrada
- **WHEN** una generacion arranca
- **THEN** el agente validador se ejecuta antes que el agente web y el agente de codigo, y ninguno de los dos se lanza si el validador no da un veredicto afirmativo

### Requirement: Error si falla una entrada imprescindible
El sistema SHALL marcar la generacion en estado de error, con el mensaje de la causa, si el validador rechaza las tecnologias o falla, si falla el agente de codigo, si falla el agente de ejercicios, o si falla el agente web cuando era la unica fuente de entrada (sin repositorio).

#### Scenario: El validador rechaza las tecnologias
- **WHEN** el validador determina que las tecnologias introducidas no son tecnologias de programacion
- **THEN** la generacion queda en estado de error con el mensaje de la causa, y no se invoca a ningun agente de entrada

#### Scenario: Falla el agente validador
- **WHEN** el agente validador termina en fallo (transporte, tiempo excedido, bloqueo de guardarrail o respuesta invalida)
- **THEN** la generacion queda en estado de error con el mensaje del fallo, y no se invoca a ningun agente de entrada

#### Scenario: Falla el agente de codigo
- **WHEN** el agente de codigo termina en fallo
- **THEN** la generacion queda en estado de error con el mensaje del fallo, y el agente de ejercicios no se llega a lanzar

#### Scenario: Falla el agente web sin repositorio
- **WHEN** el agente web termina en fallo y la generacion no tiene repositorio
- **THEN** la generacion queda en estado de error, porque no queda ninguna entrada para el agente de ejercicios

#### Scenario: Falla el agente de ejercicios
- **WHEN** el agente web (y el de codigo, si aplica) terminan con exito pero el agente de ejercicios falla
- **THEN** la generacion queda en estado de error con el mensaje del fallo

### Requirement: Trazabilidad unificada en Langfuse
El sistema SHALL propagar un unico identificador de traza de Langfuse a todos los agentes de una misma generacion (validador, web, codigo y ejercicios), de modo que sus llamadas aparezcan agrupadas en una sola traza.

#### Scenario: Generacion con repositorio y los tres agentes
- **WHEN** una generacion con repositorio llega a Ready
- **THEN** las llamadas del agente web, del agente de codigo y del agente de ejercicios aparecen bajo el mismo identificador de traza en Langfuse

#### Scenario: Traza del validador en la misma generacion
- **WHEN** una generacion arranca y el validador da un veredicto afirmativo
- **THEN** la llamada del agente validador aparece bajo el mismo identificador de traza que las de los agentes web, de codigo y de ejercicios
