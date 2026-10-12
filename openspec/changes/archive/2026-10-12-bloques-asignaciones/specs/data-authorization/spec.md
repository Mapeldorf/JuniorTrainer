# Spec Delta

## ADDED Requirements

### Requirement: Un bloque con alguna respuesta ya registrada es inmutable
Una vez que exista al menos una fila de `answer` para cualquier asignacion de un `block`, el sistema SHALL impedir cambios a su `name` y a su composicion (`block_exercise`); `deleted_at` SHALL seguir siendo modificable para poder eliminarlo.

#### Scenario: Editar el nombre de un bloque ya resuelto
- **WHEN** se intenta actualizar `name` de un `block` que tiene al menos una `answer` registrada en cualquiera de sus asignaciones
- **THEN** la base de datos rechaza la operacion

#### Scenario: Anadir o quitar un ejercicio de un bloque ya resuelto
- **WHEN** se intenta insertar o eliminar una fila de `block_exercise` de un `block` que tiene al menos una `answer` registrada en cualquiera de sus asignaciones
- **THEN** la base de datos rechaza la operacion

#### Scenario: Eliminar logicamente un bloque ya resuelto
- **WHEN** se actualiza solo `deleted_at` de un `block` que tiene alguna `answer` registrada
- **THEN** la base de datos acepta la operacion
