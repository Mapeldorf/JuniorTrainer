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

### Requirement: Buscar ejercicios manualmente en el selector del formulario de bloque
El formulario de crear/editar bloque SHALL mantener el texto escrito en el campo de busqueda del selector de ejercicios como un borrador que no recarga el listado por si solo; el listado SHALL recargarse por texto unicamente cuando el tech lead confirma la busqueda pulsando un boton "Buscar" o la tecla Enter en el campo. El filtro por tipo SHALL seguir recargando el listado automaticamente al cambiarlo, sin necesidad de confirmacion.

#### Scenario: Escribir sin confirmar no lanza busqueda
- **WHEN** un tech lead escribe texto en el campo de busqueda del selector de ejercicios sin pulsar "Buscar" ni Enter
- **THEN** el listado de ejercicios no se recarga y sigue mostrando los resultados de la ultima busqueda confirmada

#### Scenario: Confirmar la busqueda con el boton
- **WHEN** un tech lead escribe un texto en el campo de busqueda y pulsa el boton "Buscar"
- **THEN** el listado se recarga mostrando los ejercicios que coinciden con ese texto

#### Scenario: Confirmar la busqueda con Enter
- **WHEN** un tech lead escribe un texto en el campo de busqueda y pulsa Enter
- **THEN** el listado se recarga mostrando los ejercicios que coinciden con ese texto, igual que si hubiera pulsado "Buscar"

#### Scenario: Cambiar el filtro de tipo sigue siendo automatico
- **WHEN** un tech lead cambia el filtro de tipo en el selector de ejercicios
- **THEN** el listado se recarga inmediatamente con ese filtro, sin necesidad de pulsar "Buscar"
