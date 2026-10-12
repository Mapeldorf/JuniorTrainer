# Spec Delta

## MODIFIED Requirements

### Requirement: Listar y ver el detalle de un bloque
El sistema SHALL permitir a un tech lead listar sus bloques (activos y eliminados por separado), con un resumen de los alumnos asignados a cada uno y si esta resuelto, y ver el detalle de uno, incluyendo sus ejercicios, si cada uno de ellos esta eliminado de la app y si el bloque esta resuelto.

#### Scenario: Listar bloques activos
- **WHEN** un tech lead lista los bloques sin pedir los eliminados
- **THEN** devuelve solo los bloques con `deleted_at` nulo

#### Scenario: Listar bloques eliminados
- **WHEN** un tech lead pide la lista de "Bloques eliminados"
- **THEN** devuelve solo los bloques con `deleted_at` informado

#### Scenario: Ver el detalle de un bloque
- **WHEN** un tech lead consulta el detalle de un bloque, eliminado o no
- **THEN** devuelve su nombre y sus ejercicios en orden

#### Scenario: El listado incluye un resumen de los alumnos asignados
- **WHEN** un tech lead lista sus bloques
- **THEN** cada bloque incluye cuantos alumnos lo tienen asignado y quienes son

#### Scenario: El detalle marca los ejercicios eliminados de la app
- **WHEN** un tech lead consulta el detalle de un bloque que contiene un ejercicio eliminado de la app desde que se anadio al bloque
- **THEN** ese ejercicio aparece marcado como eliminado en la respuesta, sin afectar al resto de su composicion

#### Scenario: El listado y el detalle indican si el bloque esta resuelto
- **WHEN** un tech lead lista sus bloques o consulta el detalle de uno
- **THEN** cada bloque indica si esta resuelto (alguna de sus asignaciones tiene al menos una respuesta registrada)
