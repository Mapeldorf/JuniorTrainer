# Spec Delta

## MODIFIED Requirements

### Requirement: Listar las generaciones pendientes
El sistema SHALL permitir a un tech lead listar las generaciones que estan en curso (`generating`) o listas para revisar (`ready`), para que pueda verlas y actuar sobre ellas sin conocer su identificador. Las generaciones en estado `error` SHALL quedar fuera de este listado, aunque sigan almacenadas y consultables por su identificador.

#### Scenario: Listar generaciones pendientes
- **WHEN** un tech lead lista las generaciones
- **THEN** recibe las que estan en curso o listas para revisar, sin incluir las ya cerradas (`done`)

#### Scenario: Las generaciones en error no aparecen en el listado
- **WHEN** un tech lead lista las generaciones y alguna de ellas esta en estado `error`
- **THEN** el listado no incluye esa generacion, solo las que estan en curso o listas para revisar

#### Scenario: No hay generaciones pendientes
- **WHEN** un tech lead lista las generaciones y no hay ninguna en curso ni lista para revisar
- **THEN** recibe una lista vacia

## ADDED Requirements

### Requirement: Aviso de generaciones fallidas en la interfaz
El sistema SHALL mostrar en la interfaz de la lista de ejercicios un mensaje de error agregado cuando una generacion lanzada desde la sesion de navegador del tech lead termina en estado `error`, indicando cuantas generaciones han fallado. El sistema SHALL NOT mostrar esa generacion en la lista.

#### Scenario: Una generacion lanzada termina en error
- **WHEN** una generacion lanzada desde la sesion termina en estado `error`
- **THEN** la interfaz muestra un mensaje de error agregado indicando que la generacion ha fallado, y esa generacion no aparece en la lista

#### Scenario: Varias generaciones lanzadas terminan en error
- **WHEN** dos generaciones lanzadas desde la sesion terminan en estado `error`
- **THEN** la interfaz muestra un mensaje de error agregado indicando que dos generaciones han fallado

#### Scenario: Una generacion lanzada termina con exito
- **WHEN** una generacion lanzada desde la sesion termina en estado `ready`
- **THEN** la interfaz no muestra ningun mensaje de error por esa generacion, y aparece en la lista de pendientes
