# technology-validation Specification

## Purpose
Define la validacion de que las tecnologias introducidas en una generacion son tecnologias relacionadas con la programacion antes de arrancar el flujo, mediante un agente juez default-deny, con pre-filtro determinista de datos personales y guardarrailes de bloqueo.

## Requirements

### Requirement: Validacion de tecnologias como puerta previa a la generacion
El sistema SHALL validar, antes de invocar a los agentes de entrada (web, codigo y ejercicios), que las tecnologias introducidas son tecnologias relacionadas con la programacion, mediante un agente validador dedicado, y SHALL continuar con la generacion unicamente si el validador da un veredicto afirmativo.

#### Scenario: Tecnologias validas
- **WHEN** se inicia una generacion cuyas tecnologias son todas tecnologias de programacion reconocibles
- **THEN** el validador da un veredicto afirmativo y la generacion continua con los agentes de entrada

#### Scenario: Tecnologias no tecnologicas
- **WHEN** al menos una de las tecnologias introducidas no es una tecnologia de programacion
- **THEN** el validador rechaza la entrada, la generacion queda en estado de error y no se invoca a ningun agente de entrada

### Requirement: Decision default-deny del validador
El validador SHALL dar un veredicto afirmativo unicamente cuando todas las entradas sean tecnologias de programacion claramente reconocibles, y SHALL rechazar ante cualquier duda, ambiguedad, desconocimiento o texto que no sea una tecnologia de programacion.

#### Scenario: Entrada clara
- **WHEN** las tecnologias introducidas son inequivocamente tecnologias de programacion
- **THEN** el validador da un veredicto afirmativo

#### Scenario: Entrada ambigua o desconocida
- **WHEN** alguna de las entradas es ambigua, desconocida o no es una tecnologia de programacion
- **THEN** el validador da un veredicto negativo

### Requirement: Salida estructurada estricta del validador
El validador SHALL requerir del modelo un veredicto en un formato estructurado estricto e inequivoco, y SHALL dar la tarea por fallida si la respuesta no se ajusta a ese formato, sin interpretarla nunca como un veredicto afirmativo.

#### Scenario: Respuesta conforme
- **WHEN** el modelo devuelve un veredicto que cumple el formato estructurado exigido
- **THEN** el validador usa ese veredicto para decidir si la generacion continua

#### Scenario: Respuesta no conforme
- **WHEN** el modelo devuelve una respuesta que no cumple el formato estructurado exigido
- **THEN** la tarea del validador se da por fallida y la generacion queda en estado de error

### Requirement: Pre-filtro determinista de PII e identificadores
El validador SHALL rechazar, antes de invocar al modelo, cualquier entrada que coincida con un patron de dato personal o identificador (email, telefono, IBAN o documento nacional de identidad o extranjero), sin depender de la decision del modelo.

#### Scenario: Entrada con un documento de identidad
- **WHEN** una de las tecnologias introducidas coincide con un patron de documento nacional de identidad o extranjero
- **THEN** el validador rechaza la entrada sin llegar a invocar al modelo

#### Scenario: Entrada sin datos personales
- **WHEN** ninguna tecnologia coincide con un patron de dato personal o identificador
- **THEN** el pre-filtro no rechaza y la validacion continua con el modelo

### Requirement: Guardarrailes de bloqueo en las llamadas del validador
El sistema SHALL aplicar a toda llamada del validador al proveedor del modelo, tanto en su modelo principal como en el de respaldo, la deteccion de PII en modo de bloqueo (rechaza la llamada si detecta un dato personal) y la deteccion de prompt injection en modo de bloqueo (rechaza la llamada si detecta un intento), de forma independiente de la decision del modelo.

#### Scenario: Input con un dato personal
- **WHEN** el input de una llamada del validador contiene un dato personal detectable por el guardarrail de PII
- **THEN** la llamada se rechaza y la generacion queda en estado de error

#### Scenario: Input con un intento de prompt injection
- **WHEN** el input de una llamada del validador contiene un intento de prompt injection detectable por el guardarrail de injection
- **THEN** la llamada se rechaza y la generacion queda en estado de error

#### Scenario: Input limpio
- **WHEN** el input de una llamada del validador no contiene PII ni un intento detectable
- **THEN** los guardarrailes lo dejan pasar y la validacion continua con normalidad

### Requirement: Revalidacion de los limites de entrada en el validador
El validador SHALL revalidar de forma independiente los mismos limites de numero y longitud de tecnologias que aplica el backend, de modo que una peticion fuera de limite se rechace aunque no haya pasado por esa validacion.

#### Scenario: Entrada dentro de los limites
- **WHEN** el validador recibe un numero y una longitud de tecnologias dentro de los limites configurados
- **THEN** la validacion continua con normalidad

#### Scenario: Entrada fuera de limite
- **WHEN** el validador recibe mas tecnologias que el maximo permitido, o una tecnologia mas larga que el maximo permitido
- **THEN** la tarea del validador se da por fallida sin invocar al modelo con esa entrada

### Requirement: Fallo del validador es fatal para la generacion
El sistema SHALL marcar la generacion en estado de error si el validador no puede emitir un veredicto (fallo de transporte, tiempo excedido, bloqueo por guardarrail, fallo al consultar el catalogo de tecnologias, o respuesta invalida), y SHALL NOT degradar la generacion ni omitir la validacion en ese caso.

#### Scenario: El validador no responde o falla
- **WHEN** el agente validador no responde dentro del limite de tiempo o falla por cualquier causa
- **THEN** la generacion queda en estado de error y no se invoca a ningun agente de entrada

#### Scenario: No se omite la validacion
- **WHEN** el validador falla
- **THEN** el sistema no continua la generacion como si las tecnologias fueran validas

#### Scenario: Falla la consulta del catalogo de tecnologias
- **WHEN** el validador no consigue consultar el catalogo completo de tecnologias para la comprobacion semantica de duplicados
- **THEN** la tarea del validador se da por fallida y la generacion queda en estado de error, sin tratar la entrada como si no tuviera duplicados

### Requirement: Comprobacion semantica de duplicados contra el catalogo
El validador SHALL comparar cada tecnologia de entrada contra el nombre de cada tecnologia del catalogo completo, y SHALL dar un veredicto negativo para esa entrada cuando ya este cubierta semanticamente por una tecnologia existente con otro nombre, variante o abreviatura, indicando con que tecnologia existente coincide.

#### Scenario: Entrada cubierta por una tecnologia existente con otro nombre
- **WHEN** una de las tecnologias introducidas es una variante, sinonimo o abreviatura clara de una tecnologia que ya esta en el catalogo (por ejemplo, "Angular" cuando el catalogo ya tiene "Angular Framework")
- **THEN** el validador da un veredicto negativo para esa entrada, señalando con que tecnologia existente del catalogo coincide

#### Scenario: Entrada sin coincidencia en el catalogo
- **WHEN** ninguna de las tecnologias introducidas coincide semanticamente con ninguna tecnologia del catalogo
- **THEN** la comprobacion de duplicados no rechaza ninguna entrada y la validacion continua con normalidad

### Requirement: Coherencia del veredicto ante duplicados detectados
El validador SHALL tratar como no valido, igual que una respuesta con tecnologias invalidas, cualquier veredicto que declare `valid=true` a la vez que señala una coincidencia semantica con el catalogo.

#### Scenario: Veredicto afirmativo con una coincidencia señalada
- **WHEN** la respuesta del modelo trae `valid=true` junto con al menos una coincidencia semantica con el catalogo
- **THEN** el validador trata el veredicto como no valido en lugar de como una confirmacion
