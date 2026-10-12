# Spec Delta

## ADDED Requirements

### Requirement: Listar las generaciones pendientes
El sistema SHALL permitir a un tech lead listar las generaciones que no estan en estado `done` (en curso, listas para revisar, o en error), para que pueda verlas y actuar sobre ellas sin conocer su identificador.

#### Scenario: Listar generaciones pendientes
- **WHEN** un tech lead lista las generaciones
- **THEN** recibe las que estan en curso, listas para revisar, o en error, sin incluir las ya cerradas (`done`)

#### Scenario: No hay generaciones pendientes
- **WHEN** un tech lead lista las generaciones y no hay ninguna en curso, lista para revisar, o en error
- **THEN** recibe una lista vacia

### Requirement: Cierre de la revision de una generacion
El sistema SHALL permitir a un tech lead cerrar la revision de una generacion lista (`ready`), pasandola a `done`; a partir de ese momento SHALL dejar de aparecer en el listado de generaciones pendientes, independientemente de si quedan candidatos suyos sin guardar.

#### Scenario: Cerrar la revision de una generacion lista
- **WHEN** un tech lead cierra la revision de una generacion en estado `ready`
- **THEN** la generacion pasa a `done` y deja de aparecer en el listado de generaciones pendientes

#### Scenario: Cerrar la revision con candidatos sin guardar
- **WHEN** un tech lead cierra la revision de una generacion que tiene candidatos sin guardar
- **THEN** la generacion pasa a `done` igualmente, y esos candidatos quedan sin guardar

#### Scenario: Intentar cerrar la revision de una generacion que no esta lista
- **WHEN** se intenta cerrar la revision de una generacion en curso o en error
- **THEN** la peticion se rechaza y la generacion no cambia de estado
