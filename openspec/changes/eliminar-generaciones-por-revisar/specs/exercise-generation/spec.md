# Spec Delta

## ADDED Requirements

### Requirement: Eliminar una generacion por revisar
El sistema SHALL permitir a un tech lead eliminar una generacion en estado `ready` junto con todos sus ejercicios candidatos (no guardados), de modo que deje de aparecer en el listado de generaciones pendientes. El sistema SHALL rechazar la eliminacion de una generacion que no este en `ready` o que tenga algun ejercicio ya guardado como definitivo.

#### Scenario: Eliminar una generacion lista
- **WHEN** un tech lead elimina una generacion en estado `ready`
- **THEN** la generacion y todos sus ejercicios candidatos se eliminan, y la generacion deja de aparecer en el listado de generaciones pendientes

#### Scenario: Eliminar una generacion en curso
- **WHEN** se intenta eliminar una generacion en estado `generating`
- **THEN** la peticion se rechaza y la generacion no cambia

#### Scenario: Eliminar una generacion con ejercicios ya guardados
- **WHEN** se intenta eliminar una generacion `ready` que tiene al menos un ejercicio con `saved = true`
- **THEN** la peticion se rechaza y no se elimina ni la generacion ni ninguno de sus ejercicios

#### Scenario: Eliminar una generacion inexistente
- **WHEN** se intenta eliminar una generacion cuyo identificador no existe
- **THEN** la peticion responde 404 y no se elimina nada

#### Scenario: Un alumno no puede eliminar generaciones
- **WHEN** un usuario con `role = student` intenta eliminar una generacion
- **THEN** la peticion responde 403 y la generacion no cambia

### Requirement: Boton de eliminacion en el listado de generaciones por revisar
La pantalla de ejercicios SHALL mostrar un boton "Eliminar" a la derecha del boton "Revisar" en cada generacion en estado `ready` del listado de generaciones pendientes, y SHALL mostrar, antes de eliminar, un dialogo de confirmacion que advierta de que se van a eliminar los ejercicios de esa generacion; al confirmar SHALL eliminar la generacion y quitarla del listado, y al cancelar SHALL no cambiar nada.

#### Scenario: El boton solo aparece en generaciones listas
- **WHEN** el listado de pendientes contiene una generacion en estado `generating` y otra en estado `ready`
- **THEN** solo la generacion `ready` muestra el boton "Eliminar", junto al boton "Revisar"

#### Scenario: Confirmar la eliminacion de una generacion
- **WHEN** el tech lead pulsa "Eliminar" en una generacion `ready` y confirma en el dialogo de advertencia
- **THEN** la generacion se elimina y desaparece del listado de pendientes

#### Scenario: Cancelar la eliminacion de una generacion
- **WHEN** el tech lead pulsa "Eliminar" en una generacion `ready` y cancela en el dialogo de advertencia
- **THEN** la generacion sigue en el listado de pendientes sin cambios

#### Scenario: Falla la eliminacion de una generacion
- **WHEN** el tech lead confirma la eliminacion y la peticion falla
- **THEN** la pantalla muestra un mensaje de error y la generacion sigue en el listado de pendientes