# exercise-blocks Specification

## Purpose

Define el ciclo de vida de un bloque de ejercicios definitivos: crearlo, editar su nombre y su composicion mientras nadie lo haya resuelto, listarlo/verlo, y eliminarlo sin afectar a quien ya lo tiene asignado.

## Requirements

### Requirement: Crear un bloque de ejercicios
El sistema SHALL permitir a un tech lead crear un bloque con un nombre y entre 1 y 100 ejercicios definitivos.

#### Scenario: Crear un bloque valido
- **WHEN** un tech lead crea un bloque con un nombre y entre 1 y 100 ejercicios definitivos existentes
- **THEN** el bloque se crea con esos ejercicios en el orden indicado

#### Scenario: Crear un bloque fuera de rango
- **WHEN** se intenta crear un bloque con 0 ejercicios o con mas de 100
- **THEN** la peticion se rechaza y no se crea ningun bloque

#### Scenario: Crear un bloque con un ejercicio no definitivo
- **WHEN** se intenta crear un bloque indicando un ejercicio candidato o ya eliminado
- **THEN** la peticion se rechaza y no se crea ningun bloque

### Requirement: Listar y ver el detalle de un bloque
El sistema SHALL permitir a un tech lead listar sus bloques (activos y eliminados por separado) y ver el detalle de uno, incluyendo sus ejercicios.

#### Scenario: Listar bloques activos
- **WHEN** un tech lead lista los bloques sin pedir los eliminados
- **THEN** devuelve solo los bloques con `deleted_at` nulo

#### Scenario: Listar bloques eliminados
- **WHEN** un tech lead pide la lista de "Bloques eliminados"
- **THEN** devuelve solo los bloques con `deleted_at` informado

#### Scenario: Ver el detalle de un bloque
- **WHEN** un tech lead consulta el detalle de un bloque, eliminado o no
- **THEN** devuelve su nombre y sus ejercicios en orden

### Requirement: Editar un bloque solo si nadie lo ha resuelto
El sistema SHALL permitir a un tech lead editar el nombre y la composicion de un bloque (anadir o quitar ejercicios definitivos) unicamente mientras ninguna de sus asignaciones tenga todavia una respuesta registrada; quitar un ejercicio de un bloque SHALL dejar intacto su `deleted_at` en la tabla de ejercicios.

#### Scenario: Editar un bloque sin respuestas
- **WHEN** un tech lead edita el nombre o la composicion de un bloque cuyas asignaciones, si existen, no tienen ninguna respuesta
- **THEN** la edicion se aplica

#### Scenario: Editar un bloque ya resuelto por algun alumno
- **WHEN** un tech lead intenta editar el nombre o la composicion de un bloque con al menos una respuesta registrada en cualquiera de sus asignaciones
- **THEN** la peticion se rechaza y el bloque no cambia

#### Scenario: Quitar un ejercicio de un bloque no lo elimina de la app
- **WHEN** un tech lead quita un ejercicio de un bloque editable
- **THEN** el ejercicio sigue disponible como definitivo, sin `deleted_at`, para anadirse a otros bloques

### Requirement: Eliminar un bloque sin afectar a quien lo tiene asignado
El sistema SHALL permitir a un tech lead eliminar un bloque, pasandolo a "Bloques eliminados": deja de poder asignarse a nuevos alumnos, pero sigue visible en solo lectura con sus resultados, y la vista de cualquier alumno ya asignado SHALL permanecer igual.

#### Scenario: Eliminar un bloque
- **WHEN** un tech lead elimina un bloque
- **THEN** el bloque pasa a "Bloques eliminados", ya no puede asignarse a nadie nuevo, y sigue consultable en solo lectura con sus asignaciones y resultados existentes

#### Scenario: Un alumno ya asignado no nota el cambio
- **WHEN** se elimina un bloque que un alumno ya tenia asignado
- **THEN** ese alumno sigue viendo exactamente los mismos ejercicios y puede seguir respondiendolos con normalidad
