# exercise-catalog Specification

## Purpose

Define como un ejercicio generado pasa a ser definitivo, como se encuentra entre los definitivos para componer un bloque, y que efecto tiene eliminarlo de la app.

## Requirements

### Requirement: Guardar un ejercicio candidato como definitivo
El sistema SHALL permitir a un tech lead marcar como definitivo (`saved = true`) un ejercicio candidato (`saved = false`, no eliminado) de una generacion; a partir de ese momento el ejercicio SHALL volverse inmutable salvo su `deleted_at`.

#### Scenario: Guardar un candidato
- **WHEN** un tech lead guarda un ejercicio candidato existente, no guardado y no eliminado
- **THEN** el ejercicio pasa a `saved = true` y queda disponible para anadirse a bloques

#### Scenario: Intentar guardar un ejercicio ya guardado o eliminado
- **WHEN** se intenta guardar un ejercicio cuyo `saved` ya es `true`, o cuyo `deleted_at` no es nulo
- **THEN** la peticion se rechaza y el ejercicio no cambia

#### Scenario: Un alumno no puede guardar ejercicios
- **WHEN** un usuario con `role = student` intenta guardar un ejercicio candidato
- **THEN** la peticion responde 403 y el ejercicio no cambia

### Requirement: Listar y buscar ejercicios definitivos
El sistema SHALL permitir a un tech lead listar los ejercicios definitivos (`saved = true`, no eliminados), filtrables por tipo y buscables por texto en el enunciado.

#### Scenario: Listar sin filtros
- **WHEN** un tech lead lista los ejercicios definitivos sin ningun filtro
- **THEN** devuelve todos los ejercicios con `saved = true` y `deleted_at` nulo, sin candidatos ni eliminados

#### Scenario: Filtrar por tipo
- **WHEN** un tech lead lista los ejercicios definitivos indicando un tipo (`knowledge` o `debug`)
- **THEN** devuelve solo los ejercicios definitivos de ese tipo

#### Scenario: Buscar por texto
- **WHEN** un tech lead lista los ejercicios definitivos indicando un texto de busqueda
- **THEN** devuelve solo los ejercicios definitivos cuyo enunciado contiene ese texto

### Requirement: Eliminar logicamente un ejercicio definitivo
El sistema SHALL permitir a un tech lead eliminar un ejercicio definitivo marcando su `deleted_at`, de modo que deje de aparecer en el listado de definitivos y de poder anadirse a bloques nuevos, sin alterar los bloques que ya lo contengan ni las copias de asignacion ya creadas.

#### Scenario: Eliminar un ejercicio definitivo
- **WHEN** un tech lead elimina un ejercicio con `saved = true`
- **THEN** el ejercicio queda con `deleted_at` informado, deja de aparecer en el listado de definitivos, y la base de datos rechaza anadirlo a cualquier bloque nuevo

#### Scenario: Eliminar un ejercicio ya usado en bloques o asignaciones
- **WHEN** se elimina un ejercicio definitivo que ya forma parte de uno o mas bloques, o de copias de asignacion ya creadas
- **THEN** esos bloques y esas copias de asignacion no cambian
