# Spec Delta

## Purpose

Define el catálogo canónico de tecnologías seleccionables en el sistema y su consulta de solo lectura por parte del tech lead, de modo que las tecnologías usadas en una generación sean valores conocidos y estables.

## ADDED Requirements

### Requirement: Catálogo canónico de tecnologías
El sistema SHALL mantener un catálogo de tecnologías seleccionables, cada una con un nombre canónico único y no vacío, de modo que una misma tecnología tenga siempre un único identificador textual estable.

#### Scenario: Nombres canónicos únicos
- **WHEN** se inspecciona el catálogo de tecnologías
- **THEN** ninguna tecnología se repite y cada una tiene un nombre canónico único y no vacío

### Requirement: Consulta del catálogo por el tech lead
El sistema SHALL permitir a un tech lead obtener la lista completa de tecnologías del catálogo mediante una operación de solo lectura, y esa operación SHALL NOT modificar el catálogo.

#### Scenario: El tech lead lista el catálogo
- **WHEN** un tech lead solicita la lista de tecnologías
- **THEN** recibe todas las tecnologías del catálogo con su nombre canónico

#### Scenario: Un alumno no puede consultar el catálogo
- **WHEN** un usuario con `role = student` solicita la lista de tecnologías
- **THEN** la petición responde 403 y no devuelve el catálogo

### Requirement: Tecnologías del catálogo relacionadas con Angular
El catálogo SHALL incluir, desde el despliegue inicial, las tecnologías relacionadas con Angular cuyo conjunto concreto se fija en design.md.

#### Scenario: El catálogo arranca con tecnologías de Angular
- **WHEN** se consulta el catálogo tras el despliegue inicial
- **THEN** devuelve las tecnologías relacionadas con Angular fijadas en design.md