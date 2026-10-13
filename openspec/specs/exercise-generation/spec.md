# exercise-generation Specification

## Purpose

Define como el sistema, a partir de unas tecnologias y opcionalmente un repositorio, orquesta tres agentes de IA por A2A para producir de 1 a 5 ejercicios candidatos, con sus limites y su manejo de fallos parciales.

## Requirements

### Requirement: Entrada minima de una generacion
El sistema SHALL requerir al menos las tecnologias para iniciar una generacion; el repositorio SHALL ser opcional.

#### Scenario: Generacion solo con tecnologias
- **WHEN** se inicia una generacion con una lista de tecnologias y sin repositorio
- **THEN** la generacion arranca sin lanzar el agente de codigo

#### Scenario: Generacion sin tecnologias
- **WHEN** se intenta iniciar una generacion sin ninguna tecnologia indicada
- **THEN** la peticion se rechaza y no se crea ninguna generacion

### Requirement: Orquestacion en paralelo de los agentes de entrada
El sistema SHALL lanzar el agente web y, si hay repositorio, el agente de codigo en paralelo, SHALL esperar a que ambos terminen, y SHALL enviar sus resultados junto con el tipo de ejercicio y el numero pedido al agente de ejercicios.

#### Scenario: Generacion con repositorio
- **WHEN** una generacion incluye repositorio
- **THEN** el agente web y el agente de codigo se ejecutan a la vez, y el agente de ejercicios solo recibe el mensaje despues de que ambos han terminado

#### Scenario: Generacion sin repositorio
- **WHEN** una generacion no incluye repositorio
- **THEN** el agente de codigo no se ejecuta, y el agente de ejercicios recibe solo el resultado del agente web

### Requirement: Numero de ejercicios candidatos
El sistema SHALL producir entre 1 y 5 ejercicios candidatos por generacion, segun lo pedido, sin guardarlos automaticamente.

#### Scenario: Se piden 3 candidatos
- **WHEN** una generacion pide 3 ejercicios y termina en Ready
- **THEN** devuelve exactamente 3 ejercicios candidatos, ninguno marcado como guardado

#### Scenario: Se pide un numero fuera de rango
- **WHEN** se solicita una generacion con un numero de ejercicios menor que 1 o mayor que 5
- **THEN** la peticion se rechaza y no se crea ninguna generacion

### Requirement: Estado de la generacion
El sistema SHALL exponer el estado de una generacion como en curso, lista (Ready) con sus candidatos, o en error con un mensaje describiendo la causa.

#### Scenario: Consultar una generacion en curso
- **WHEN** se consulta una generacion cuyos agentes todavia no han terminado
- **THEN** el estado devuelto indica que sigue en curso, sin candidatos todavia

#### Scenario: Consultar una generacion terminada con exito
- **WHEN** se consulta una generacion cuyo agente de ejercicios ha terminado correctamente
- **THEN** el estado es Ready y devuelve la lista de candidatos

### Requirement: Degradacion si falla el agente web habiendo repositorio
El sistema SHALL continuar la generacion sin fuentes de internet si el agente web falla y hay un repositorio disponible como entrada adicional para el agente de ejercicios.

#### Scenario: Falla el agente web, hay repositorio
- **WHEN** el agente web termina en fallo y la generacion tiene repositorio
- **THEN** la generacion continua con el resultado del agente de codigo, sin resumen de tecnologias de internet, y termina en Ready si el resto del flujo tiene exito

### Requirement: Error si falla una entrada imprescindible
El sistema SHALL marcar la generacion en estado de error, con el mensaje de la causa, si falla el agente de codigo, si falla el agente de ejercicios, o si falla el agente web cuando era la unica fuente de entrada (sin repositorio).

#### Scenario: Falla el agente de codigo
- **WHEN** el agente de codigo termina en fallo
- **THEN** la generacion queda en estado de error con el mensaje del fallo, y el agente de ejercicios no se llega a lanzar

#### Scenario: Falla el agente web sin repositorio
- **WHEN** el agente web termina en fallo y la generacion no tiene repositorio
- **THEN** la generacion queda en estado de error, porque no queda ninguna entrada para el agente de ejercicios

#### Scenario: Falla el agente de ejercicios
- **WHEN** el agente web (y el de codigo, si aplica) terminan con exito pero el agente de ejercicios falla
- **THEN** la generacion queda en estado de error con el mensaje del fallo

### Requirement: Limites de tiempo de la generacion
El sistema SHALL limitar cada tarea A2A a un maximo de 2 minutos y la generacion completa a un maximo de 5 minutos, marcando como error la generacion que supere cualquiera de los dos limites.

#### Scenario: Una tarea A2A se excede
- **WHEN** una tarea A2A individual supera los 2 minutos sin responder
- **THEN** esa tarea se da por fallida y se aplica la regla de error o degradacion que corresponda a ese agente

#### Scenario: La generacion completa se excede
- **WHEN** el conjunto de la generacion supera los 5 minutos sin llegar a Ready
- **THEN** la generacion queda en estado de error por tiempo excedido

### Requirement: Generacion no se ejecuta en la peticion HTTP
El sistema SHALL ejecutar la orquestacion de los agentes en una tarea de fondo, de modo que la peticion que inicia una generacion SHALL responder antes de que los agentes terminen.

#### Scenario: Iniciar una generacion
- **WHEN** se llama al endpoint que inicia una generacion
- **THEN** la respuesta llega de inmediato con un identificador de generacion, sin esperar a que los agentes terminen

### Requirement: Trazabilidad unificada en Langfuse
El sistema SHALL propagar un unico identificador de traza de Langfuse a los tres agentes de una misma generacion, de modo que sus llamadas aparezcan agrupadas en una sola traza.

#### Scenario: Generacion con repositorio y los tres agentes
- **WHEN** una generacion con repositorio llega a Ready
- **THEN** las llamadas del agente web, del agente de codigo y del agente de ejercicios aparecen bajo el mismo identificador de traza en Langfuse

### Requirement: Listar las generaciones pendientes
El sistema SHALL permitir a un tech lead listar las generaciones que no estan en estado `done` (en curso, listas para revisar, o en error), para que pueda verlas y actuar sobre ellas sin conocer su identificador.

#### Scenario: Listar generaciones pendientes
- **WHEN** un tech lead lista las generaciones
- **THEN** recibe las que estan en curso, listas para revisar, o en error, sin incluir las ya cerradas (`done`)

#### Scenario: No hay generaciones pendientes
- **WHEN** un tech lead lista las generaciones y no hay ninguna en curso, lista para revisar, o en error
- **THEN** recibe una lista vacia

### Requirement: Cierre de la revision de una generacion
El sistema SHALL permitir a un tech lead cerrar la revision de una generacion lista (`ready`), pasandola a `done`; a partir de ese momento SHALL dejar de aparecer en el listado de generaciones pendientes, independientemente de si quedan candidatos suyos sin guardar.

#### Scenario: Cerrar la revision de una generacion lista
- **WHEN** un tech lead cierra la revision de una generacion en estado `ready`
- **THEN** la generacion pasa a `done` y deja de aparecer en el listado de generaciones pendientes

#### Scenario: Cerrar la revision con candidatos sin guardar
- **WHEN** un tech lead cierra la revision de una generacion que tiene candidatos sin guardar
- **THEN** la generacion pasa a `done` igualmente, y esos candidatos quedan sin guardar

#### Scenario: Intentar cerrar la revision de una generacion que no esta lista
- **WHEN** se intenta cerrar la revision de una generacion en curso o en error
- **THEN** la peticion se rechaza y la generacion no cambia de estado

### Requirement: Nivel junior de los ejercicios candidatos
El sistema SHALL producir candidatos resolubles por un desarrollador junior recien incorporado a un proyecto: cada candidato SHALL tratar un unico concepto y SHALL ser resoluble con el enunciado y el codigo de apoyo que se le entregan, sin pedir redisenos, refactors, cambios en varios ficheros ni decisiones de arquitectura.

#### Scenario: Candidato de tipo knowledge
- **WHEN** una generacion de tipo `knowledge` llega a Ready
- **THEN** cada candidato pregunta por un unico concepto de las tecnologias de la generacion, respondible sin consultar nada mas que lo que se entrega con el ejercicio

#### Scenario: Candidato de tipo debug
- **WHEN** una generacion de tipo `debug` llega a Ready
- **THEN** cada candidato pide encontrar y corregir un unico fallo dentro del codigo de apoyo que se entrega, sin pedir reescribir ni reorganizar el resto

#### Scenario: Un candidato pediria rediseno o varios pasos
- **WHEN** el agente de ejercicios redacta un candidato que exigiria redisenar, refactorizar o recorrer varios ficheros
- **THEN** ese candidato no se devuelve como resultado de la generacion

### Requirement: Longitud maxima del enunciado
El sistema SHALL limitar el enunciado de cada candidato a 50 palabras como maximo, contando como palabra cada secuencia de caracteres separada por espacios en blanco. El codigo de apoyo y la respuesta esperada no cuentan para ese limite.

#### Scenario: Enunciados de una generacion lista
- **WHEN** una generacion llega a Ready con sus candidatos
- **THEN** el enunciado de cada candidato tiene 50 palabras o menos

#### Scenario: Un enunciado se pasa del limite
- **WHEN** al redactar los candidatos alguno sale con un enunciado de mas de 50 palabras
- **THEN** se vuelven a pedir los candidatos indicando que acorten los enunciados que se pasaban, una sola vez

#### Scenario: El enunciado sigue pasandose tras el segundo intento
- **WHEN** tras ese segundo intento algun enunciado sigue teniendo mas de 50 palabras
- **THEN** la tarea del agente de ejercicios se da por fallida y la generacion queda en estado de error, sin devolver candidatos que incumplan el limite

### Requirement: Codigo de apoyo acotado
El sistema SHALL acotar el codigo de apoyo de cada candidato a un unico fragmento breve de un solo fichero, y SHALL dejarlo vacio en los candidatos de tipo `knowledge` que se entienden sin codigo. En los candidatos de tipo `debug` el codigo de apoyo SHALL contener exactamente un fallo introducido a proposito.

#### Scenario: Candidato knowledge que no necesita codigo
- **WHEN** un candidato de tipo `knowledge` se entiende solo con su enunciado
- **THEN** su codigo de apoyo se devuelve vacio

#### Scenario: Candidato debug con su codigo de apoyo
- **WHEN** una generacion de tipo `debug` llega a Ready
- **THEN** cada candidato trae un unico fragmento de un solo fichero, con exactamente un fallo introducido a proposito
