# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
