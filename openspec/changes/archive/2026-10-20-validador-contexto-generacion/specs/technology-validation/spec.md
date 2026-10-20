# Spec Delta

## MODIFIED Requirements

### Requirement: Validacion de tecnologias como puerta previa a la generacion
El sistema SHALL validar, antes de invocar a los agentes de entrada (web, codigo y ejercicios), que las tecnologias introducidas son tecnologias relacionadas con la programacion, mediante un agente validador dedicado, y SHALL continuar con la generacion unicamente si el validador da un veredicto afirmativo. En este contexto, el validador SHALL comprobar unicamente que cada entrada es una tecnologia de programacion, y SHALL NOT comparar las entradas contra el catalogo de tecnologias existentes ni rechazarlas por coincidir con una tecnologia ya existente.

#### Scenario: Tecnologias validas
- **WHEN** se inicia una generacion cuyas tecnologias son todas tecnologias de programacion reconocibles
- **THEN** el validador da un veredicto afirmativo y la generacion continua con los agentes de entrada

#### Scenario: Tecnologias no tecnologicas
- **WHEN** al menos una de las tecnologias introducidas no es una tecnologia de programacion
- **THEN** el validador rechaza la entrada, la generacion queda en estado de error y no se invoca a ningun agente de entrada

#### Scenario: Tecnologia ya existente en el catalogo
- **WHEN** se inicia una generacion con una tecnologia que ya esta en el catalogo con ese mismo nombre, o que el validador consideraria una variante semantica de una tecnologia ya existente
- **THEN** el validador no la rechaza por ese motivo, y la generacion continua si la entrada es una tecnologia de programacion reconocible

### Requirement: Comprobacion semantica de duplicados contra el catalogo
Cuando valida un alta de tecnologia en el catalogo, el validador SHALL comparar la tecnologia de entrada contra el nombre de cada tecnologia del catalogo completo, y SHALL dar un veredicto negativo cuando ya este cubierta semanticamente por una tecnologia existente con otro nombre, variante o abreviatura, indicando con que tecnologia existente coincide. Esta comprobacion SHALL NOT aplicarse cuando el validador valida las tecnologias de una generacion de ejercicios.

#### Scenario: Entrada cubierta por una tecnologia existente con otro nombre
- **WHEN** se da de alta una tecnologia que es una variante, sinonimo o abreviatura clara de una tecnologia que ya esta en el catalogo (por ejemplo, "Angular" cuando el catalogo ya tiene "Angular Framework")
- **THEN** el validador da un veredicto negativo para esa entrada, señalando con que tecnologia existente del catalogo coincide

#### Scenario: Entrada sin coincidencia en el catalogo
- **WHEN** ninguna de las tecnologias de un alta coincide semanticamente con ninguna tecnologia del catalogo
- **THEN** la comprobacion de duplicados no rechaza ninguna entrada y la validacion continua con normalidad

### Requirement: Fallo del validador es fatal para la generacion
El sistema SHALL marcar la generacion en estado de error si el validador no puede emitir un veredicto (fallo de transporte, tiempo excedido, bloqueo por guardarrail, fallo al consultar el catalogo de tecnologias durante un alta, o respuesta invalida), y SHALL NOT degradar la generacion ni omitir la validacion en ese caso.

#### Scenario: El validador no responde o falla
- **WHEN** el agente validador no responde dentro del limite de tiempo o falla por cualquier causa
- **THEN** la generacion queda en estado de error y no se invoca a ningun agente de entrada

#### Scenario: No se omite la validacion
- **WHEN** el validador falla
- **THEN** el sistema no continua la generacion como si las tecnologias fueran validas

#### Scenario: Falla la consulta del catalogo de tecnologias
- **WHEN** el validador no consigue consultar el catalogo completo de tecnologias para la comprobacion semantica de duplicados durante un alta
- **THEN** la tarea del validador se da por fallida, sin tratar la entrada como si no tuviera duplicados
