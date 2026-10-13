# Spec Delta

## ADDED Requirements

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
