# Spec Delta

## MODIFIED Requirements

### Requirement: Rechazo de tecnologías duplicadas en el alta
El sistema SHALL rechazar dar de alta una tecnologia que ya existe en el catalogo, comparando sin distinguir mayusculas ni espacios sobrantes, y SHALL NOT crear una fila duplicada. Ademas, SHALL rechazar dar de alta una tecnologia que el agente validador identifique como semanticamente cubierta por una tecnologia ya existente con otro nombre, variante o abreviatura, devolviendo con que tecnologia existente coincide.

#### Scenario: Nombre ya existente
- **WHEN** un tech lead da de alta una tecnologia cuyo nombre ya esta en el catalogo
- **THEN** la peticion se rechaza y el catalogo no cambia

#### Scenario: Variante de mayúsculas o espacios de un nombre existente
- **WHEN** un tech lead da de alta una tecnologia que coincide con una existente salvo por mayúsculas o espacios sobrantes
- **THEN** la peticion se rechaza y el catalogo no cambia

#### Scenario: Variante semantica de un nombre existente
- **WHEN** un tech lead da de alta una tecnologia que el agente validador identifica como la misma tecnologia que una ya existente en el catalogo, aunque el nombre no coincida de forma exacta
- **THEN** la peticion se rechaza indicando con que tecnologia existente coincide, y el catalogo no cambia
