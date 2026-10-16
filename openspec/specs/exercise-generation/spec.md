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
El sistema SHALL propagar un unico identificador de traza de Langfuse a todos los agentes de una misma generacion (validador, web, codigo y ejercicios), de modo que sus llamadas aparezcan agrupadas en una sola traza.

#### Scenario: Generacion con repositorio y los tres agentes
- **WHEN** una generacion con repositorio llega a Ready
- **THEN** las llamadas del agente web, del agente de codigo y del agente de ejercicios aparecen bajo el mismo identificador de traza en Langfuse

#### Scenario: Traza del validador en la misma generacion
- **WHEN** una generacion arranca y el validador da un veredicto afirmativo
- **THEN** la llamada del agente validador aparece bajo el mismo identificador de traza que las de los agentes web, de codigo y de ejercicios

### Requirement: Listar las generaciones pendientes
El sistema SHALL permitir a un tech lead listar las generaciones que estan en curso (`generating`) o listas para revisar (`ready`), para que pueda verlas y actuar sobre ellas sin conocer su identificador. Las generaciones en estado `error` SHALL quedar fuera de este listado, aunque sigan almacenadas y consultables por su identificador.

#### Scenario: Listar generaciones pendientes
- **WHEN** un tech lead lista las generaciones
- **THEN** recibe las que estan en curso o listas para revisar, sin incluir las ya cerradas (`done`)

#### Scenario: Las generaciones en error no aparecen en el listado
- **WHEN** un tech lead lista las generaciones y alguna de ellas esta en estado `error`
- **THEN** el listado no incluye esa generacion, solo las que estan en curso o listas para revisar

#### Scenario: No hay generaciones pendientes
- **WHEN** un tech lead lista las generaciones y no hay ninguna en curso ni lista para revisar
- **THEN** recibe una lista vacia

### Requirement: Aviso de generaciones fallidas en la interfaz
El sistema SHALL mostrar en la interfaz de la lista de ejercicios un mensaje de error agregado cuando una generacion lanzada desde la sesion de navegador del tech lead termina en estado `error`, indicando cuantas generaciones han fallado. El sistema SHALL NOT mostrar esa generacion en la lista.

#### Scenario: Una generacion lanzada termina en error
- **WHEN** una generacion lanzada desde la sesion termina en estado `error`
- **THEN** la interfaz muestra un mensaje de error agregado indicando que la generacion ha fallado, y esa generacion no aparece en la lista

#### Scenario: Varias generaciones lanzadas terminan en error
- **WHEN** dos generaciones lanzadas desde la sesion terminan en estado `error`
- **THEN** la interfaz muestra un mensaje de error agregado indicando que dos generaciones han fallado

#### Scenario: Una generacion lanzada termina con exito
- **WHEN** una generacion lanzada desde la sesion termina en estado `ready`
- **THEN** la interfaz no muestra ningun mensaje de error por esa generacion, y aparece en la lista de pendientes

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

### Requirement: Nombre de cada ejercicio candidato
El sistema SHALL producir, para cada ejercicio candidato, un nombre corto (distinto del enunciado) de 8 palabras como maximo, contando como palabra cada secuencia de caracteres separada por espacios en blanco, que lo identifique de un vistazo sin repetir el enunciado completo.

#### Scenario: Candidatos de una generacion lista
- **WHEN** una generacion llega a Ready con sus candidatos
- **THEN** cada candidato trae un nombre de 8 palabras o menos, distinto de su enunciado

#### Scenario: Un nombre se pasa del limite
- **WHEN** al redactar los candidatos algun nombre sale con mas de 8 palabras
- **THEN** se vuelven a pedir los candidatos indicando que acorten los nombres que se pasaban, una sola vez

#### Scenario: El nombre sigue pasandose tras el segundo intento
- **WHEN** tras ese segundo intento algun nombre sigue teniendo mas de 8 palabras
- **THEN** la tarea del agente de ejercicios se da por fallida y la generacion queda en estado de error, sin devolver candidatos que incumplan el limite

### Requirement: Tipo de ejercicio exige repositorio salvo conocimiento
El sistema SHALL rechazar una generación de tipo `debug` o `both` que no incluya repositorio, aceptando sin repositorio únicamente el tipo `knowledge`.

#### Scenario: Debug sin repositorio
- **WHEN** se intenta iniciar una generación de tipo `debug` sin repositorio
- **THEN** la petición se rechaza y no se crea ninguna generación

#### Scenario: Both sin repositorio
- **WHEN** se intenta iniciar una generación de tipo `both` sin repositorio
- **THEN** la petición se rechaza y no se crea ninguna generación

#### Scenario: Knowledge sin repositorio
- **WHEN** se inicia una generación de tipo `knowledge` sin repositorio
- **THEN** la petición se acepta y la generación arranca con normalidad

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
