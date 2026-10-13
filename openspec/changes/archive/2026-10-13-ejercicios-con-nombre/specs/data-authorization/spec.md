# Spec Delta

## MODIFIED Requirements

### Requirement: Un ejercicio guardado es inmutable
Una vez que un `exercise` tiene `saved = true`, el sistema SHALL impedir cambios a su nombre, enunciado, codigo, tipo, generacion de origen o respuesta esperada; `deleted_at` SHALL seguir siendo modificable para poder eliminarlo de la aplicacion.

#### Scenario: Intentar editar el enunciado de un ejercicio guardado
- **WHEN** se intenta actualizar `statement` de un `exercise` cuyo `saved` ya es `true`
- **THEN** la base de datos rechaza la operacion

#### Scenario: Intentar editar el nombre de un ejercicio guardado
- **WHEN** se intenta actualizar `name` de un `exercise` cuyo `saved` ya es `true`
- **THEN** la base de datos rechaza la operacion

#### Scenario: Eliminar un ejercicio guardado
- **WHEN** se actualiza solo `deleted_at` de un `exercise` cuyo `saved` ya es `true`
- **THEN** la base de datos acepta la operacion
